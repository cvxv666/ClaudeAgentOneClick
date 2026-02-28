"""Ingest pipelines: audio transcription and document processing."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from brain.config import VAULT_PATH, GROQ_KEY_FILE
from brain.vault import frontmatter
from brain.vault.tools import _trigger_sync, _trigger_embedding_update

_GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_GROQ_MODEL = "whisper-large-v3"

# Paths that should never be ingested (security: prevent credential leaks)
_BLOCKED_PATH_PATTERNS = (".env", ".ssh", "webhook", "token", "credential", "secret", "api-key", "api_key")


def _check_ingest_path(file_path: str) -> str | None:
    """Return error message if file_path looks like a credential file."""
    lower = file_path.lower()
    for pattern in _BLOCKED_PATH_PATTERNS:
        if pattern in lower:
            return f"Blocked: path '{file_path}' matches sensitive pattern '{pattern}'"
    return None

# Groq limit: 25MB per request
_GROQ_MAX_BYTES = 25 * 1024 * 1024
# Audio longer than this (seconds) goes to Groq API; shorter stays local
_LOCAL_MAX_DURATION = 240  # 4 minutes


def _get_groq_key() -> str | None:
    """Read Groq API key from config file."""
    if not GROQ_KEY_FILE.exists():
        return None
    try:
        data = json.loads(GROQ_KEY_FILE.read_text())
        return data.get("api_key")
    except Exception:
        return None


def _get_audio_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _split_audio_for_groq(src: Path) -> list[Path]:
    """Split audio into <=24MB chunks (MP3) for Groq API limit."""
    file_size = src.stat().st_size
    if file_size <= _GROQ_MAX_BYTES:
        return [src]

    duration = _get_audio_duration(src)
    if duration <= 0:
        return [src]

    target_chunk_bytes = 20 * 1024 * 1024
    n_chunks = max(2, int(file_size / target_chunk_bytes) + 1)
    chunk_duration = duration / n_chunks

    tmp_dir = Path(tempfile.mkdtemp(prefix="groq_chunks_"))
    chunks: list[Path] = []

    for i in range(n_chunks):
        start = i * chunk_duration
        chunk_path = tmp_dir / f"chunk_{i:03d}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-ss", str(start),
             "-t", str(chunk_duration), "-ac", "1", "-ar", "16000",
             "-b:a", "64k", chunk_path],
            capture_output=True, timeout=120,
        )
        if chunk_path.exists():
            chunks.append(chunk_path)

    return chunks if chunks else [src]


def _transcribe_groq(src: Path, api_key: str) -> tuple[str, str]:
    """Transcribe audio via Groq Whisper API. Returns (text, language)."""
    import httpx

    chunks = _split_audio_for_groq(src)
    all_text: list[str] = []
    language = "unknown"

    for chunk_path in chunks:
        with open(chunk_path, "rb") as f:
            resp = httpx.post(
                _GROQ_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (chunk_path.name, f, "audio/mpeg")},
                data={
                    "model": _GROQ_MODEL,
                    "response_format": "verbose_json",
                },
                timeout=120.0,
            )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("text", "")
        if text:
            all_text.append(text.strip())
        if data.get("language"):
            language = data["language"]

    # Clean up temp chunks
    for chunk_path in chunks:
        if chunk_path != src and chunk_path.exists():
            chunk_path.unlink()
            if chunk_path.parent.name.startswith("groq_chunks_"):
                try:
                    chunk_path.parent.rmdir()
                except OSError:
                    pass

    return "\n\n".join(all_text), language


def _transcribe_local(src: Path) -> tuple[str, float, str]:
    """Transcribe audio locally with faster-whisper. Returns (text, duration, language)."""
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(src), word_timestamps=True)

    parts: list[str] = []
    current_chunk: list[str] = []
    current_tokens = 0

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        current_chunk.append(text)
        current_tokens += len(text.split())

        gap = 0.0
        if hasattr(segment, "end") and hasattr(segment, "start"):
            gap = getattr(segment, "end", 0) - getattr(segment, "start", 0)

        if current_tokens >= 500 or gap > 3.0:
            parts.append(" ".join(current_chunk))
            current_chunk = []
            current_tokens = 0

    if current_chunk:
        parts.append(" ".join(current_chunk))

    full_text = "\n\n".join(parts)
    return full_text, info.duration, info.language


def vault_ingest_audio(file_path: str, title: str = "") -> str:
    """Transcribe an audio file and save to the vault.

    Routing: <=4min -> local faster-whisper (CPU), >4min -> Groq API.
    Falls back between backends on failure.
    """
    blocked = _check_ingest_path(file_path)
    if blocked:
        return blocked

    src = Path(file_path)
    if not src.exists():
        return f"File not found: {file_path}"

    duration = _get_audio_duration(src)
    groq_key = _get_groq_key()
    use_groq = groq_key and duration > _LOCAL_MAX_DURATION

    if use_groq:
        try:
            full_text, language = _transcribe_groq(src, groq_key)
            model_used = f"groq/{_GROQ_MODEL}"
        except Exception as e:
            try:
                full_text, duration, language = _transcribe_local(src)
                model_used = "whisper-base (fallback)"
            except ImportError:
                return f"Groq API failed ({e}) and faster-whisper not installed."
    else:
        try:
            full_text, duration, language = _transcribe_local(src)
            model_used = "whisper-base"
        except ImportError:
            if groq_key:
                try:
                    full_text, language = _transcribe_groq(src, groq_key)
                    model_used = f"groq/{_GROQ_MODEL} (fallback)"
                except Exception as e:
                    return f"Both backends failed. Groq: {e}"
            else:
                return "No transcription backend: install faster-whisper or set Groq API key."

    if not full_text.strip():
        return "Transcription produced no text."

    # Build document
    now = datetime.now().astimezone()
    doc_title = title or _slugify(src.stem)
    subdir = now.strftime("%Y-%m")
    slug = _slugify(doc_title)

    meta = frontmatter.make_meta(
        doc_title,
        tags=["audio", "transcript"],
        source="audio",
        duration=f"{duration:.0f}s",
        language=language,
        model=model_used,
    )

    body = f"## Transcript\n\n{full_text}"
    content = frontmatter.render(meta, body)

    rel_path = f"audio/{subdir}/{slug}.md"
    dest = VAULT_PATH / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")

    _trigger_sync()
    _trigger_embedding_update(rel_path)
    return f"Transcribed and saved: {rel_path} ({duration:.0f}s, {language}, {model_used})"


def vault_ingest_document(file_path: str, title: str = "", chunk_size: int = 2000) -> str:
    """Process a text/PDF document and save to the vault as chunks."""
    blocked = _check_ingest_path(file_path)
    if blocked:
        return blocked

    src = Path(file_path)
    if not src.exists():
        return f"File not found: {file_path}"

    suffix = src.suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf(src)
    elif suffix in (".txt", ".md", ".rst", ".csv", ".json"):
        text = src.read_text(encoding="utf-8", errors="replace")
    else:
        return f"Unsupported file type: {suffix}. Supported: .pdf, .txt, .md, .rst, .csv, .json"

    if not text.strip():
        return "Document is empty."

    doc_title = title or _slugify(src.stem)
    slug = _slugify(doc_title)

    words = text.split()
    chunks: list[str] = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)

    if len(chunks) == 1:
        meta = frontmatter.make_meta(
            doc_title,
            tags=["document"],
            source=suffix.lstrip("."),
        )
        body = f"## Content\n\n{chunks[0]}"
        content = frontmatter.render(meta, body)
        rel_path = f"documents/{slug}.md"
        dest = VAULT_PATH / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        _trigger_sync()
        _trigger_embedding_update(rel_path)
        return f"Saved: {rel_path} ({len(words)} words)"

    # Multiple chunks
    base_dir = VAULT_PATH / "documents" / slug
    base_dir.mkdir(parents=True, exist_ok=True)

    overview_meta = frontmatter.make_meta(
        doc_title,
        tags=["document", "overview"],
        source=suffix.lstrip("."),
        chunks=len(chunks),
    )
    chunk_links = "\n".join(
        f"- [[{slug}/chunk-{i+1:03d}|Part {i+1}]]"
        for i in range(len(chunks))
    )
    overview_body = f"## Overview\n\nDocument split into {len(chunks)} parts ({len(words)} words total).\n\n## Parts\n\n{chunk_links}"
    overview = frontmatter.render(overview_meta, overview_body)
    (base_dir / "_overview.md").write_text(overview, encoding="utf-8")

    for i, chunk in enumerate(chunks):
        chunk_meta = frontmatter.make_meta(
            f"{doc_title} — Part {i+1}",
            tags=["document", "chunk"],
            source=suffix.lstrip("."),
            parent=f"documents/{slug}/_overview.md",
            chunk_index=i + 1,
            total_chunks=len(chunks),
        )
        chunk_body = f"## Content\n\n{chunk}"
        chunk_content = frontmatter.render(chunk_meta, chunk_body)
        (base_dir / f"chunk-{i+1:03d}.md").write_text(chunk_content, encoding="utf-8")

    _trigger_sync()
    _trigger_embedding_update(f"documents/{slug}/_overview.md")
    for i in range(len(chunks)):
        _trigger_embedding_update(f"documents/{slug}/chunk-{i+1:03d}.md")
    return f"Saved: documents/{slug}/ ({len(chunks)} chunks, {len(words)} words)"


def _read_pdf(path: Path) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            return result.stdout
    except Exception:
        pass
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")[:80]
