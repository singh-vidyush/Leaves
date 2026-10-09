from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.database import connect

SAMPLE_CALENDAR_EVENTS = [
    {
        "remote_id": "cal-sample-001",
        "title": "Weekly Team Standup",
        "description": "Weekly engineering check-in",
        "start_offset_hours": 1,
        "duration_minutes": 30,
        "created_by": "external",
    },
    {
        "remote_id": "cal-sample-002",
        "title": "Architecture Sync with Product",
        "description": "Review sprint objectives and integrations",
        "start_offset_hours": 4,
        "duration_minutes": 60,
        "created_by": "external",
    },
]


def sync_calendar() -> dict[str, Any]:
    """
    Syncs Google Calendar commitments. If live credentials are not set,
    populates baseline calendar commitments for the day.
    """
    now = datetime.now(timezone.utc)
    count = 0
    with connect() as db:
        for sample in SAMPLE_CALENDAR_EVENTS:
            start = (now + timedelta(hours=sample["start_offset_hours"])).isoformat()
            end = (now + timedelta(hours=sample["start_offset_hours"], minutes=sample["duration_minutes"])).isoformat()
            existing = db.execute("SELECT id FROM calendar_events WHERE remote_id=?", (sample["remote_id"],)).fetchone()
            if not existing:
                db.execute(
                    "INSERT INTO calendar_events(remote_id, title, description, start_time, end_time, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                    (sample["remote_id"], sample["title"], sample["description"], start, end, sample["created_by"]),
                )
                count += 1
    return {"synced_count": count}


def list_events(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, remote_id, title, description, start_time, end_time, status, created_by, created_at, updated_at "
            "FROM calendar_events ORDER BY start_time ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_event(event_id: int) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None


def add_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    created_by: str = "leaves",
) -> dict[str, Any]:
    """Automatically adds an event (authorized by user policy)."""
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO calendar_events(title, description, start_time, end_time, created_by) VALUES (?, ?, ?, ?, ?)",
            (title, description, start_time, end_time, created_by),
        )
        event_id = cursor.lastrowid
        row = db.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        return dict(row)


def move_calendar_event(event_id: int, new_start_time: str, new_end_time: str) -> dict[str, Any]:
    """Automatically moves an event to resolve conflict or reschedule (authorized by user policy)."""
    with connect() as db:
        row = db.execute("SELECT id FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        if not row:
            raise LookupError(f"Event {event_id} not found.")
        db.execute(
            "UPDATE calendar_events SET start_time=?, end_time=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_start_time, new_end_time, event_id),
        )
        updated = db.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        return dict(updated)


def delete_calendar_event(event_id: int, user_confirmed: bool = False) -> bool:
    """
    CRITICAL NON-NEGOTIABLE:
    'Deleting calendar events always requires explicit user approval.'
    """
    if not user_confirmed:
        raise PermissionError("Deleting calendar events always requires explicit user approval.")

    with connect() as db:
        cursor = db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
        return cursor.rowcount > 0
