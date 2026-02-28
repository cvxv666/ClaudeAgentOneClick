"""Core vault MCP tools: search, read, write, list."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from brain.config import VAULT_PATH
from brain.vault import frontmatter


def _resolve(path: str) -> Path:
    """Resolve a vault-relative path safely (with symlink protection)."""
    vault_root = str(VAULT_PATH.resolve())
    p = (VAULT_PATH / path).resolve()
    if not str(p).startswith(vault_root):
        raise ValueError(f"Path escapes vault: {path}")
    # Check for symlinks pointing outside vault
    check = VAULT_PATH / path
    for part in [check] + list(check.parents):
        if part == VAULT_PATH or not str(part).startswith(str(VAULT_PATH)):
            break
        if part.is_symlink() and not str(part.resolve()).startswith(vault_root):
            raise ValueError(f"Symlink escapes vault: {path}")
    return p


def _resolve_folder(folder: str) -> Path:
    """Resolve a folder parameter safely."""
    if not folder:
        return VAULT_PATH
    vault_root = str(VAULT_PATH.resolve())
    p = (VAULT_PATH / folder).resolve()
    if not str(p).startswith(vault_root):
        raise ValueError(f"Folder escapes vault: {folder}")
    if not p.is_dir():
        raise ValueError(f"Folder not found: {folder}")
    return p


def vault_search(query: str, folder: str = "", tags: str = "") -> str:
    """Full-text search across the vault."""
    try:
        search_path = _resolve_folder(folder)
    except ValueError as e:
        return str(e)

    try:
        result = subprocess.run(
            ["grep", "-rni", "--include=*.md", query, str(search_path)],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return "Search timed out."

    lines = result.stdout.strip().splitlines()
    if not lines:
        return f"No results for '{query}'"

    # Filter by tags if specified
    tag_filter = {t.strip() for t in tags.split(",") if t.strip()} if tags else set()
    if tag_filter:
        filtered = []
        seen_files: set[str] = set()
        for line in lines:
            fpath = line.split(":")[0]
            if fpath in seen_files:
                continue
            seen_files.add(fpath)
            try:
                meta, _ = frontmatter.parse(Path(fpath).read_text(encoding="utf-8"))
                file_tags = set(meta.get("tags", []))
                if tag_filter & file_tags:
                    filtered.extend(l for l in lines if l.startswith(fpath + ":"))
            except Exception:
                continue
        lines = filtered

    # Limit output and format nicely
    prefix = str(VAULT_PATH) + "/"
    output_lines = []
    for line in lines[:50]:
        output_lines.append(line.replace(prefix, ""))

    total = len(lines)
    result_text = "\n".join(output_lines)
    if total > 50:
        result_text += f"\n\n... and {total - 50} more matches"
    return result_text


def vault_read(path: str) -> str:
    """Read a document from the vault."""
    p = _resolve(path)
    if not p.exists():
        return f"File not found: {path}"
    if not p.is_file():
        return f"Not a file: {path}"
    return p.read_text(encoding="utf-8")


def vault_write(
    path: str,
    content: str,
    title: str = "",
    tags: str = "",
    source: str = "",
) -> str:
    """Create or update a document in the vault."""
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    doc_title = title or p.stem.replace("-", " ").replace("_", " ").title()

    # If content already has frontmatter, keep it
    meta, body = frontmatter.parse(content)
    if not meta:
        meta = frontmatter.make_meta(doc_title, tag_list, source)
        body = content

    full_content = frontmatter.render(meta, body)
    p.write_text(full_content, encoding="utf-8")

    # Trigger async git sync (non-blocking)
    _trigger_sync()

    # Trigger async embedding index update
    _trigger_embedding_update(path)

    return f"Written: {path} ({len(full_content)} bytes)"


def vault_list(folder: str = "", tags: str = "") -> str:
    """List documents in the vault."""
    try:
        search_path = _resolve_folder(folder)
    except ValueError as e:
        return str(e)

    tag_filter = {t.strip() for t in tags.split(",") if t.strip()} if tags else set()

    entries = []
    for md in sorted(search_path.rglob("*.md")):
        # Skip hidden dirs and templates
        rel = md.relative_to(VAULT_PATH)
        parts = rel.parts
        if any(p.startswith(".") for p in parts):
            continue
        if parts[0] == "templates":
            continue

        try:
            meta, _ = frontmatter.parse(md.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

        file_tags = meta.get("tags", [])

        if tag_filter and not (tag_filter & set(file_tags)):
            continue

        title = meta.get("title", rel.stem)
        tag_str = ", ".join(file_tags) if file_tags else ""
        size = md.stat().st_size
        line = f"  {rel}  —  {title}"
        if tag_str:
            line += f"  [{tag_str}]"
        line += f"  ({size}b)"
        entries.append(line)

    if not entries:
        return f"No documents found in {folder or '/'}" + (
            f" with tags [{tags}]" if tags else ""
        )

    header = f"Vault: {folder or '/'} ({len(entries)} files)\n"
    return header + "\n".join(entries)


def vault_update_dashboard(action: str, task: str, project: str = "", date: str = "") -> str:
    """Safely update dashboard.md without overwriting existing data."""
    from datetime import datetime as _dt

    if action not in ("add", "complete", "remove"):
        return f"Unknown action '{action}'. Use: add, complete, remove."

    if not date:
        date = _dt.now().astimezone().strftime("%Y-%m-%d")

    p = VAULT_PATH / "dashboard.md"
    if not p.exists():
        return "dashboard.md not found in vault."

    text = p.read_text(encoding="utf-8")
    meta, body = frontmatter.parse(text)

    # Split body into sections
    lines = body.splitlines()
    active_start = -1
    completed_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("## Active"):
            active_start = i
        elif line.strip().startswith("## Completed"):
            completed_start = i

    if active_start == -1 or completed_start == -1:
        return "dashboard.md missing '## Active Tasks' or '## Completed' section."

    # Extract active and completed sections
    active_lines = lines[active_start + 1:completed_start]
    completed_lines = lines[completed_start + 1:]

    if action == "add":
        if not project:
            return "Project is required for 'add' action."
        new_line = f"- [ ] **[{project}]** {task} ({date})"
        active_lines.append(new_line)
        result_msg = f"Added to active: [{project}] {task}"

    elif action == "complete":
        found_idx = -1
        found_line = ""
        task_lower = task.lower()
        for i, line in enumerate(active_lines):
            if task_lower in line.lower() and line.strip().startswith("- [ ]"):
                found_idx = i
                found_line = line
                break

        if found_idx == -1:
            return f"No active task matching '{task}' found."

        active_lines.pop(found_idx)
        completed_entry = found_line.replace("- [ ]", "- [x]").rstrip()
        import re
        completed_entry = re.sub(r"\(\d{4}-\d{2}-\d{2}\)\s*$", "", completed_entry).rstrip()
        completed_entry += f" (done: {date})"
        completed_lines.append(completed_entry)
        result_msg = f"Completed: {found_line.strip()}"

    elif action == "remove":
        found_idx = -1
        task_lower = task.lower()
        for i, line in enumerate(active_lines):
            if task_lower in line.lower():
                found_idx = i
                break

        if found_idx == -1:
            return f"No active task matching '{task}' found."

        removed = active_lines.pop(found_idx)
        result_msg = f"Removed: {removed.strip()}"

    # Rebuild file
    new_lines = lines[:active_start + 1]
    new_lines.extend(active_lines)
    if new_lines and new_lines[-1].strip():
        new_lines.append("")
    new_lines.append("## Completed")
    new_lines.extend(completed_lines)

    new_body = "\n".join(new_lines)
    if not meta:
        meta = frontmatter.make_meta("Dashboard", ["dashboard", "tasks"])
    full_content = frontmatter.render(meta, new_body)
    p.write_text(full_content, encoding="utf-8")

    _trigger_sync()
    return result_msg


def _trigger_sync() -> None:
    """Fire-and-forget git sync. Errors are silently ignored."""
    try:
        from brain.vault.sync import schedule_sync
        schedule_sync()
    except Exception:
        pass


def _trigger_embedding_update(path: str) -> None:
    """Fire-and-forget embedding index update for a single document."""
    try:
        from brain.vault.embeddings import update_single_document
        import threading
        t = threading.Thread(target=update_single_document, args=(path,), daemon=True)
        t.start()
    except Exception:
        pass
