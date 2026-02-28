"""Parse and generate YAML frontmatter for Obsidian-compatible markdown."""

from __future__ import annotations

import re
from datetime import datetime

import yaml

_FM_RE = re.compile(r"^---\n(.+?)\n---\n?", re.DOTALL)


def parse(text: str) -> tuple[dict, str]:
    """Split markdown into (frontmatter_dict, body).

    Returns empty dict if no frontmatter found.
    """
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    body = text[m.end():]
    return meta, body


def render(meta: dict, body: str) -> str:
    """Combine frontmatter dict and body into markdown string."""
    fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm}---\n\n{body}"


def make_meta(
    title: str,
    tags: list[str] | None = None,
    source: str = "",
    **extra: object,
) -> dict:
    """Create a standard frontmatter dict."""
    meta: dict = {
        "title": title,
        "tags": tags or [],
        "created": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if source:
        meta["source"] = source
    meta.update(extra)
    return meta
