"""Calendar tools — date info, events, week planning."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from brain.calendar.db import (
    DAYS_EN, DAYS_EN_FULL,
    add_event as db_add_event,
    list_events as db_list_events,
    remove_event as db_remove_event,
    update_event as db_update_event,
    add_sync as db_add_sync,
    list_sync_queue as db_list_sync_queue,
    clear_sync_queue as db_clear_sync_queue,
)


def _today() -> date:
    return date.today()


def _logical_today() -> date:
    """Logical 'today' with 03:00 MSK boundary.

    Before 03:00 MSK returns yesterday — for reflections and session notes.
    """
    now = datetime.now()
    if now.hour < 3:
        return (now - timedelta(days=1)).date()
    return now.date()


def _week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def _format_date(d: date) -> str:
    """Format as '03.03 (Tue)'."""
    return f"{d.strftime('%d.%m')} ({DAYS_EN[d.weekday()]})"


def _format_date_full(d: date) -> str:
    """Format as '03.03.2026 (Tuesday)'."""
    return f"{d.strftime('%d.%m.%Y')} ({DAYS_EN_FULL[d.weekday()]})"


def _parse_date(s: str) -> date:
    """Parse YYYY-MM-DD or DD.MM.YYYY or DD.MM."""
    s = s.strip()
    if not s:
        return _today()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m"):
        try:
            d = datetime.strptime(s, fmt).date()
            if fmt == "%d.%m":
                d = d.replace(year=_today().year)
            return d
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}. Use YYYY-MM-DD or DD.MM.YYYY")


def _build_week_view(start: date, events: list[dict]) -> str:
    """Build a week view with events."""
    today = _today()
    events_by_date = {}
    for e in events:
        events_by_date.setdefault(e["date"], []).append(e)

    lines = []
    for i in range(7):
        d = start + timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        marker = " ← today" if d == today else ""
        day_events = events_by_date.get(ds, [])
        line = f"  {DAYS_EN[d.weekday()]} {d.strftime('%d.%m')}{marker}"
        if day_events:
            for ev in day_events:
                time_str = f" {ev['time']}" if ev.get("time") else ""
                proj_str = f" [{ev['project']}]" if ev.get("project") else ""
                line += f"\n    • {ev['title']}{time_str}{proj_str}"
        lines.append(line)
    return "\n".join(lines)


def calendar_get_today() -> str:
    """Get current date, day of week, and week overview with events."""
    today = _today()
    week_start = _week_start(today)
    week_end = week_start + timedelta(days=6)
    iso_week = today.isocalendar()[1]

    # Get events for this week + next 2 weeks
    lookahead_end = week_start + timedelta(days=20)
    events = db_list_events(
        week_start.strftime("%Y-%m-%d"),
        lookahead_end.strftime("%Y-%m-%d"),
    )

    # This week
    this_week_events = [e for e in events if e["date"] <= week_end.strftime("%Y-%m-%d")]
    next_week_start = week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)
    next_week_events = [
        e for e in events
        if next_week_start.strftime("%Y-%m-%d") <= e["date"] <= next_week_end.strftime("%Y-%m-%d")
    ]

    logical = _logical_today()
    logical_line = ""
    if logical != today:
        logical_line = f"\n⏰ Logical day (03:00 boundary): {_format_date_full(logical)}"

    parts = [
        f"Today: {_format_date_full(today)}{logical_line}",
        f"Week: {iso_week} ({_format_date(week_start)} — {_format_date(week_end)})",
        "",
        "This week:",
        _build_week_view(week_start, this_week_events),
    ]

    if next_week_events:
        parts.extend([
            "",
            "Next week:",
            _build_week_view(next_week_start, next_week_events),
        ])

    return "\n".join(parts)


def calendar_add_event(title: str, date_str: str, time: str = "",
                       end_date: str = "", project: str = "", notes: str = "",
                       source_type: str = "", source_id: str = "") -> str:
    """Add an event or deadline to the calendar."""
    try:
        d = _parse_date(date_str)
    except ValueError as e:
        return str(e)

    event_id = db_add_event(
        title=title,
        date=d.strftime("%Y-%m-%d"),
        time=time,
        end_date=end_date,
        project=project,
        notes=notes,
        source_type=source_type,
        source_id=source_id,
    )
    return f"Event #{event_id} added: {title} on {_format_date_full(d)}" + (
        f" at {time}" if time else ""
    ) + (f" [{project}]" if project else "")


def calendar_list_events(from_date: str = "", to_date: str = "", project: str = "") -> str:
    """List events in a date range."""
    today = _today()
    try:
        start = _parse_date(from_date) if from_date else today
        end = _parse_date(to_date) if to_date else start + timedelta(days=30)
    except ValueError as e:
        return str(e)

    events = db_list_events(
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
        project,
    )

    if not events:
        proj_str = f" [{project}]" if project else ""
        return f"No events{proj_str} from {_format_date(start)} to {_format_date(end)}"

    lines = [f"Events from {_format_date(start)} to {_format_date(end)}:"]
    current_date = ""
    for e in events:
        if e["date"] != current_date:
            current_date = e["date"]
            d = _parse_date(current_date)
            lines.append(f"\n{_format_date_full(d)}:")
        time_str = f" {e['time']}" if e.get("time") else ""
        proj_str = f" [{e['project']}]" if e.get("project") else ""
        notes_str = f" — {e['notes']}" if e.get("notes") else ""
        lines.append(f"  #{e['id']} {e['title']}{time_str}{proj_str}{notes_str}")

    return "\n".join(lines)


def calendar_remove_event(event_id: str = "", title: str = "") -> str:
    """Remove an event by ID or title substring."""
    eid = int(event_id) if event_id and event_id.isdigit() else 0
    deleted = db_remove_event(event_id=eid, title_substring=title)
    if deleted:
        return f"Removed {deleted} event(s)."
    return "No matching events found."


def calendar_update_event(event_id: str, title: str = "", date_str: str = "",
                          time: str = "", project: str = "", notes: str = "",
                          source_type: str = "", source_id: str = "") -> str:
    """Update an existing event."""
    if not event_id.isdigit():
        return "event_id must be a number."

    kwargs = {}
    if title:
        kwargs["title"] = title
    if date_str:
        try:
            d = _parse_date(date_str)
            kwargs["date"] = d.strftime("%Y-%m-%d")
        except ValueError as e:
            return str(e)
    if time:
        kwargs["time"] = time
    if project:
        kwargs["project"] = project
    if notes:
        kwargs["notes"] = notes
    if source_type:
        kwargs["source_type"] = source_type
    if source_id:
        kwargs["source_id"] = source_id

    if not kwargs:
        return "Nothing to update — provide at least one field."

    ok = db_update_event(int(event_id), **kwargs)
    return f"Event #{event_id} updated." if ok else f"Event #{event_id} not found."


def calendar_queue_sync(event_id: str, action: str, new_date: str = "",
                        new_title: str = "") -> str:
    """Queue a sync action for a calendar event (processed by cron).

    Use this when updating a task status — queue removal or update of the linked calendar event.
    """
    if not event_id.isdigit():
        return "event_id must be a number."
    if action not in ("remove", "update"):
        return "action must be 'remove' or 'update'."

    sync_id = db_add_sync(int(event_id), action, new_date, new_title)
    return f"Sync #{sync_id} queued: {action} event #{event_id}" + (
        f" → {new_date}" if new_date else ""
    )
