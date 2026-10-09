from datetime import datetime, time, timedelta, timezone
from typing import Any, Optional

from app.core.database import connect
from app.integrations.connectors import get_schedule_connector

DEFAULT_SETTINGS = {
    "working_hours_start": "09:00",
    "working_hours_end": "17:00",
    "break_start": "12:00",
    "break_end": "13:00",
    "default_duration_minutes": "30",
    "notifications_enabled": "true",
}


class NoAvailableSlotError(ValueError):
    pass


def get_availability_settings() -> dict[str, str]:
    with connect() as db:
        rows = db.execute("SELECT key, value FROM settings").fetchall()
        result = dict(DEFAULT_SETTINGS)
        for r in rows:
            if r["key"] in DEFAULT_SETTINGS:
                result[r["key"]] = r["value"]
        return result


def update_availability_settings(settings: dict[str, str]) -> dict[str, str]:
    with connect() as db:
        for k, v in settings.items():
            if k in DEFAULT_SETTINGS:
                db.execute(
                    "INSERT INTO settings(key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                    (k, str(v)),
                )
    return get_availability_settings()


def list_time_away_blocks() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, title, start_time, end_time, created_at FROM time_away_blocks ORDER BY start_time"
        ).fetchall()
        return [dict(row) for row in rows]


def add_time_away_block(title: str, start_time: str, end_time: str) -> dict[str, Any]:
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Time-away dates must include a timezone.")
    if end <= start:
        raise ValueError("Time-away end must be later than its start.")
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO time_away_blocks(title, start_time, end_time) VALUES (?, ?, ?)",
            (title.strip(), start.isoformat(), end.isoformat()),
        )
        row = db.execute(
            "SELECT id, title, start_time, end_time, created_at FROM time_away_blocks WHERE id=?",
            (cursor.lastrowid,),
        ).fetchone()
        return dict(row)


def remove_time_away_block(block_id: int) -> bool:
    with connect() as db:
        cursor = db.execute("DELETE FROM time_away_blocks WHERE id=?", (block_id,))
        return cursor.rowcount > 0


def _parse_time(t_str: str) -> time:
    parts = t_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def find_next_available_slot(
    duration_minutes: int,
    target_date: Optional[datetime] = None,
) -> tuple[datetime, datetime]:
    """
    Finds the next valid slot within working hours that does not overlap
    with breaks or existing calendar commitments.
    """
    settings = get_availability_settings()
    work_start_time = _parse_time(settings["working_hours_start"])
    work_end_time = _parse_time(settings["working_hours_end"])
    break_start_time = _parse_time(settings["break_start"])
    break_end_time = _parse_time(settings["break_end"])

    now = datetime.now(timezone.utc)
    current_day = target_date or now

    # Search up to 5 days ahead
    for day_offset in range(5):
        eval_date = current_day + timedelta(days=day_offset)

        # Skip weekends
        if eval_date.weekday() >= 5:
            continue

        work_start = eval_date.replace(hour=work_start_time.hour, minute=work_start_time.minute, second=0, microsecond=0)
        work_end = eval_date.replace(hour=work_end_time.hour, minute=work_end_time.minute, second=0, microsecond=0)
        break_start = eval_date.replace(hour=break_start_time.hour, minute=break_start_time.minute, second=0, microsecond=0)
        break_end = eval_date.replace(hour=break_end_time.hour, minute=break_end_time.minute, second=0, microsecond=0)

        # Don't schedule in the past
        slot_candidate = max(work_start, now + timedelta(minutes=10))
        # Round up to nearest 15 minutes
        minute_rem = slot_candidate.minute % 15
        if minute_rem != 0:
            slot_candidate += timedelta(minutes=(15 - minute_rem))
        slot_candidate = slot_candidate.replace(second=0, microsecond=0)

        # Load calendar commitments and personal time-away blocks for this day.
        day_start = eval_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = eval_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        with connect() as db:
            events = db.execute(
                "SELECT start_time, end_time FROM calendar_events WHERE status != 'cancelled'"
            ).fetchall()
            away_blocks = db.execute("SELECT start_time, end_time FROM time_away_blocks").fetchall()

        parsed_events = []
        for e in [*events, *away_blocks]:
            try:
                s = datetime.fromisoformat(e["start_time"])
                en = datetime.fromisoformat(e["end_time"])
            except (TypeError, ValueError) as error:
                raise NoAvailableSlotError("A calendar or time-away record has an invalid timestamp.") from error
            if s.tzinfo is None or en.tzinfo is None:
                raise NoAvailableSlotError("Calendar and time-away timestamps must include a timezone.")
            if s < day_end and en > day_start:
                parsed_events.append((s, en))

        # Check candidate slots
        step = timedelta(minutes=15)
        dur = timedelta(minutes=duration_minutes)

        while slot_candidate + dur <= work_end:
            slot_end = slot_candidate + dur

            # Check break overlap
            overlap_break = not (slot_end <= break_start or slot_candidate >= break_end)
            if overlap_break:
                slot_candidate = break_end
                continue

            # Check event overlap
            overlap_event = False
            for ev_s, ev_e in parsed_events:
                if not (slot_end <= ev_s or slot_candidate >= ev_e):
                    overlap_event = True
                    slot_candidate = max(slot_candidate + step, ev_e)
                    break

            if overlap_event:
                continue
            if not overlap_event:
                return slot_candidate, slot_end

    raise NoAvailableSlotError("No available slot was found in the next five days.")


def schedule_task(task_id: int) -> dict[str, Any]:
    """
    Schedules an extracted task into the calendar respecting availability constraints.
    Creates notification on schedule update.
    """
    with connect() as db:
        task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            raise LookupError(f"Task {task_id} not found.")

    duration = int(task["suggested_duration_minutes"])
    start_dt, end_dt = find_next_available_slot(duration)

    event = get_schedule_connector("local_calendar").add_event(
        title=f"Task: {task['title']}",
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat(),
        description=f"Automated schedule for task #{task['id']}. {task['description']}",
    )

    notifications_enabled = get_availability_settings()["notifications_enabled"].lower() == "true"
    with connect() as db:
        db.execute(
            "UPDATE tasks SET status='scheduled', scheduled_event_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (event["id"], task_id),
        )
        if notifications_enabled:
            db.execute(
                "INSERT INTO notifications(title, message, event_id, task_id) VALUES (?, ?, ?, ?)",
                (
                    "Task Scheduled",
                    f"'{task['title']}' scheduled for {start_dt.strftime('%b %d at %H:%M')}.",
                    event["id"],
                    task_id,
                ),
            )

    return {"task_id": task_id, "event": event}


def resolve_conflicts_and_reschedule() -> list[dict[str, Any]]:
    """
    Checks for overlapping events and moves Leaves-managed events to next available slots.
    Never deletes events automatically.
    """
    moved_events = []
    with connect() as db:
        events = db.execute(
            "SELECT * FROM calendar_events WHERE status != 'cancelled' ORDER BY start_time ASC"
        ).fetchall()

    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1 = events[i]
            e2 = events[j]
            s1 = datetime.fromisoformat(e1["start_time"])
            e_end1 = datetime.fromisoformat(e1["end_time"])
            s2 = datetime.fromisoformat(e2["start_time"])
            e_end2 = datetime.fromisoformat(e2["end_time"])

            if not (e_end1 <= s2 or s1 >= e_end2):
                # Conflict found!
                # If e2 was created by leaves, move e2. If e1 was created by leaves, move e1.
                target = e2 if e2["created_by"] == "leaves" else (e1 if e1["created_by"] == "leaves" else None)
                if target:
                    dur_mins = int((datetime.fromisoformat(target["end_time"]) - datetime.fromisoformat(target["start_time"])).total_seconds() / 60)
                    new_start, new_end = find_next_available_slot(dur_mins)
                    updated = get_schedule_connector("local_calendar").move_event(
                        target["id"], new_start.isoformat(), new_end.isoformat()
                    )
                    moved_events.append(updated)

                    if get_availability_settings()["notifications_enabled"].lower() == "true":
                        with connect() as db:
                            db.execute(
                                "INSERT INTO notifications(title, message, event_id) VALUES (?, ?, ?)",
                                (
                                    "Schedule Conflict Resolved",
                                    f"Moved '{target['title']}' to {new_start.strftime('%b %d at %H:%M')} to avoid collision.",
                                    target["id"],
                                ),
                            )
    return moved_events
