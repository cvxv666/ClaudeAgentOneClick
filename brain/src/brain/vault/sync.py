"""Git sync for the vault — debounced auto-commit + push."""

from __future__ import annotations

import logging
import subprocess
import threading
from datetime import datetime

from brain.config import SYNC_DEBOUNCE, VAULT_PATH

log = logging.getLogger(__name__)

_lock = threading.Lock()
_pending = False
_timer: threading.Timer | None = None


def schedule_sync() -> None:
    """Schedule a debounced git sync.

    Multiple calls within SYNC_DEBOUNCE seconds are batched into one commit.
    """
    global _pending, _timer
    with _lock:
        _pending = True
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(SYNC_DEBOUNCE, _do_sync)
        _timer.daemon = True
        _timer.start()


def sync_vault() -> str:
    """Full bidirectional sync: pull -> add -> commit -> push."""
    vault = str(VAULT_PATH)
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    actions: list[str] = []

    try:
        pull = subprocess.run(
            ["git", "pull", "--rebase", "--autostash"],
            cwd=vault, capture_output=True, text=True, timeout=30,
        )
        if pull.returncode != 0:
            log.error("git pull failed: %s", pull.stderr.strip())
            return f"error: pull failed — {pull.stderr.strip()[:200]}"
        if "Already up to date" not in pull.stdout:
            actions.append("pulled")

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=vault, capture_output=True, text=True, timeout=10,
        )
        if not status.stdout.strip():
            if actions:
                return "ok: " + ", ".join(actions)
            return "ok: nothing to sync"

        subprocess.run(
            ["git", "add", "-A"],
            cwd=vault, capture_output=True, timeout=10, check=True,
        )

        changed_files = len(status.stdout.strip().splitlines())
        subprocess.run(
            ["git", "commit", "-m", f"vault: auto-sync {ts} ({changed_files} files)"],
            cwd=vault, capture_output=True, timeout=10, check=True,
        )
        actions.append(f"committed {changed_files} files")

        push = subprocess.run(
            ["git", "push"],
            cwd=vault, capture_output=True, text=True, timeout=30,
        )
        if push.returncode != 0:
            log.error("git push failed: %s", push.stderr.strip())
            return f"error: push failed — {push.stderr.strip()[:200]}"
        actions.append("pushed")

        result = "ok: " + ", ".join(actions)
        log.info("vault sync: %s", result)
        return result

    except subprocess.TimeoutExpired:
        log.error("vault sync timed out")
        return "error: timeout"
    except Exception as exc:
        log.error("vault sync error: %s", exc)
        return f"error: {exc}"


def _do_sync() -> None:
    """Debounced sync triggered by MCP write operations."""
    global _pending
    with _lock:
        if not _pending:
            return
        _pending = False

    sync_vault()
