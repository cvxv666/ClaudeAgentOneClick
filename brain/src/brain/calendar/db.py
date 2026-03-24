"""Calendar database — SQLite storage for events and deadlines."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("/root/brain/calendar.db")

DAYS_EN = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
DAYS_EN_FULL = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday",
}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            project TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            source_id TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrate existing DB: add columns if missing
    for col in ("source_type", "source_id"):
        try:
            conn.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            new_date TEXT DEFAULT '',
            new_title TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_project ON events(project)")
    conn.commit()
    return conn


def add_event(title: str, date: str, time: str = "", end_date: str = "",
              project: str = "", notes: str = "",
              source_type: str = "", source_id: str = "") -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO events (title, date, time, end_date, project, notes, source_type, source_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, date, time, end_date, project, notes, source_type, source_id),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id


def list_events(from_date: str, to_date: str, project: str = "") -> list[dict]:
    conn = _conn()
    if project:
        rows = conn.execute(
            "SELECT * FROM events WHERE date >= ? AND date <= ? AND project = ? ORDER BY date, time",
            (from_date, to_date, project),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM events WHERE date >= ? AND date <= ? ORDER BY date, time",
            (from_date, to_date),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_event(event_id: int) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_event(event_id: int, **kwargs) -> bool:
    conn = _conn()
    fields = []
    values = []
    for key in ("title", "date", "time", "end_date", "project", "notes", "source_type", "source_id"):
        if key in kwargs and kwargs[key] is not None:
            fields.append(f"{key} = ?")
            values.append(kwargs[key])
    if not fields:
        return False
    values.append(event_id)
    conn.execute(f"UPDATE events SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def remove_event(event_id: int = 0, title_substring: str = "") -> int:
    conn = _conn()
    if event_id:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    elif title_substring:
        conn.execute("DELETE FROM events WHERE title LIKE ?", (f"%{title_substring}%",))
    else:
        conn.close()
        return 0
    deleted = conn.total_changes
    conn.commit()
    conn.close()
    return deleted


# --- Sync queue ---

def add_sync(event_id: int, action: str, new_date: str = "", new_title: str = "") -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO sync_queue (event_id, action, new_date, new_title) VALUES (?, ?, ?, ?)",
        (event_id, action, new_date, new_title),
    )
    conn.commit()
    sync_id = cur.lastrowid
    conn.close()
    return sync_id


def list_sync_queue() -> list[dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM sync_queue ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_sync_queue(processed_ids: list[int] | None = None) -> int:
    conn = _conn()
    if processed_ids:
        placeholders = ",".join("?" for _ in processed_ids)
        conn.execute(f"DELETE FROM sync_queue WHERE id IN ({placeholders})", processed_ids)
    else:
        conn.execute("DELETE FROM sync_queue")
    deleted = conn.total_changes
    conn.commit()
    conn.close()
    return deleted


def list_events_with_source() -> list[dict]:
    """List all events that have a source_type (for sync checking)."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM events WHERE source_type != '' ORDER BY date",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_old_events(days: int = 14) -> int:
    """Remove events older than N days (cleanup)."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = _conn()
    conn.execute("DELETE FROM events WHERE date < ?", (cutoff,))
    deleted = conn.total_changes
    conn.commit()
    conn.close()
    return deleted
