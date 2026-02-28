"""Minimal OpenAI-compatible Whisper API server using faster-whisper.

Implements POST /v1/audio/transcriptions for compatibility with
OpenAI client libraries (like takopi's voice transcription).

Routing: audio <=4min -> local faster-whisper, >4min -> Groq API.

Run: uv run python -m brain.whisper_server
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from http.server import HTTPServer, BaseHTTPRequestHandler

from brain.config import GROQ_KEY_FILE

_model = None
_LOCAL_MAX_DURATION = 240  # 4 minutes
_GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_GROQ_MODEL = "whisper-large-v3"


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print("[whisper] Loading model 'base' (first time may be slow)...")
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        print("[whisper] Model loaded.")
    return _model


def _get_groq_key() -> str | None:
    if not GROQ_KEY_FILE.exists():
        return None
    try:
        data = json.loads(GROQ_KEY_FILE.read_text())
        return data.get("api_key")
    except Exception:
        return None


def _get_duration(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _transcribe_groq(audio_path: str, api_key: str) -> str:
    import httpx

    with open(audio_path, "rb") as f:
        resp = httpx.post(
            _GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (Path(audio_path).name, f, "audio/mpeg")},
            data={"model": _GROQ_MODEL},
            timeout=120.0,
        )
    resp.raise_for_status()
    return resp.json().get("text", "")


class WhisperHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/audio/transcriptions":
            self.send_error(404, "Not found")
            return

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if "multipart/form-data" not in content_type:
            self.send_error(400, "Expected multipart/form-data")
            return

        boundary = content_type.split("boundary=")[-1].encode()
        body = self.rfile.read(content_length)

        audio_data = self._extract_file(body, boundary)
        if not audio_data:
            self.send_error(400, "No audio file found in request")
            return

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            duration = _get_duration(temp_path)
            groq_key = _get_groq_key()

            if groq_key and duration > _LOCAL_MAX_DURATION:
                start = time.time()
                text = _transcribe_groq(temp_path, groq_key)
                elapsed = time.time() - start
                print(f"[whisper] Groq: {duration:.1f}s audio in {elapsed:.1f}s")
            else:
                model = get_model()
                start = time.time()
                segments, info = model.transcribe(temp_path)
                text = " ".join(seg.text.strip() for seg in segments)
                elapsed = time.time() - start
                print(f"[whisper] Local: {info.duration:.1f}s audio in {elapsed:.1f}s ({info.language})")
        except Exception as e:
            print(f"[whisper] Error: {e}")
            try:
                if groq_key:
                    text = _transcribe_groq(temp_path, groq_key)
                else:
                    model = get_model()
                    segments, _ = model.transcribe(temp_path)
                    text = " ".join(seg.text.strip() for seg in segments)
            except Exception as e2:
                Path(temp_path).unlink(missing_ok=True)
                self.send_error(500, f"Transcription failed: {e2}")
                return
        finally:
            Path(temp_path).unlink(missing_ok=True)

        response = json.dumps({"text": text}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _extract_file(self, body: bytes, boundary: bytes) -> bytes | None:
        parts = body.split(b"--" + boundary)
        for part in parts:
            if b'name="file"' in part or b"filename=" in part:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                data = part[header_end + 4:]
                if data.endswith(b"\r\n"):
                    data = data[:-2]
                if data.endswith(b"--"):
                    data = data[:-2]
                if data.endswith(b"\r\n"):
                    data = data[:-2]
                return data
        return None

    def log_message(self, format, *args):
        pass


def main():
    host = "127.0.0.1"
    port = 8787
    print(f"[whisper] Starting Whisper server on {host}:{port}")
    print(f"[whisper] Routing: <=4min local (base), >4min Groq ({_GROQ_MODEL})")
    print(f"[whisper] Groq key: {'found' if _get_groq_key() else 'NOT FOUND'}")
    print(f"[whisper] Endpoint: POST http://{host}:{port}/v1/audio/transcriptions")

    get_model()

    server = HTTPServer((host, port), WhisperHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[whisper] Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
