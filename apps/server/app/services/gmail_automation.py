"""Incremental Gmail task automation for the running desktop app."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.database import connect
from app.integrations.connectors import get_schedule_connector
from app.integrations.google_calendar.service import calendar_is_connected
from app.integrations.google_oauth import google_service_connected
from app.integrations.gmail.service import get_task_relevant_emails, sync_gmail
from app.services.scheduling import NoAvailableSlotError, schedule_task
from app.services.task_extraction import extract_and_store_tasks_from_context

CURSOR_KEY = "gmail_automation_cursor"
BASELINE_KEY = "gmail_automation_baseline"
SEEN_IDS_KEY = "gmail_automation_seen_ids"
URGENT_SCORE = 8
OVERLAP_MINUTES = 7
MAX_SEEN_IDS = 5000


def _get_setting(key: str) -> str | None:
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def _save_settings(values: dict[str, str]) -> None:
    with connect() as db:
        for key, value in values.items():
            db.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                (key, value),
            )


def poll_gmail_and_schedule_urgent_tasks() -> dict[str, Any]:
    """Process newly received Gmail messages and schedule urgent tasks once."""
    if not google_service_connected("gmail"):
        return {"connected": False, "baseline": False, "new_emails": 0, "new_tasks": 0, "scheduled_count": 0}

    now = datetime.now(timezone.utc)
    cursor_value = _get_setting(CURSOR_KEY)
    if cursor_value is None:
        # Establish a baseline without importing or scheduling historical mail.
        _save_settings({CURSOR_KEY: now.isoformat(), BASELINE_KEY: now.isoformat(), SEEN_IDS_KEY: "[]"})
        return {"connected": True, "baseline": True, "new_emails": 0, "new_tasks": 0, "scheduled_count": 0}

    try:
        cursor = datetime.fromisoformat(cursor_value)
        if cursor.tzinfo is None:
            cursor = cursor.replace(tzinfo=timezone.utc)
    except ValueError:
        cursor = now - timedelta(minutes=OVERLAP_MINUTES)

    seen_value = _get_setting(SEEN_IDS_KEY) or "[]"
    try:
        seen_order = json.loads(seen_value)
        if not isinstance(seen_order, list):
            seen_order = []
    except (TypeError, json.JSONDecodeError):
        seen_order = []
    seen_ids = set(seen_order)

    sync_result = sync_gmail(after_timestamp=cursor)
    baseline_value = _get_setting(BASELINE_KEY) or cursor_value
    baseline = datetime.fromisoformat(baseline_value)
    if baseline.tzinfo is None:
        baseline = baseline.replace(tzinfo=timezone.utc)

    candidates: list[str] = []
    for remote_id, date_value in sync_result.get("message_dates", []):
        try:
            message_date = datetime.fromisoformat(date_value)
            if message_date.tzinfo is None:
                message_date = message_date.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if message_date >= baseline and remote_id not in seen_ids:
            candidates.append(remote_id)

    relevant_emails = get_task_relevant_emails(limit=max(len(candidates), 1), remote_ids=candidates)
    tasks = extract_and_store_tasks_from_context(relevant_emails) if relevant_emails else []

    urgent_tasks = [
        task for task in tasks
        if task.get("source_type") == "email"
        and task.get("status") == "pending"
        and int(task.get("urgency_score", 0)) >= URGENT_SCORE
    ]
    if urgent_tasks and calendar_is_connected():
        get_schedule_connector("local_calendar").sync()

    scheduled_count = 0
    for task in urgent_tasks:
        try:
            schedule_task(int(task["id"]))
            scheduled_count += 1
        except NoAvailableSlotError:
            # Keep the task pending so it can be scheduled manually or on a later poll.
            continue

    for remote_id in candidates:
        if remote_id not in seen_ids:
            seen_order.append(remote_id)
            seen_ids.add(remote_id)
    seen_order = seen_order[-MAX_SEEN_IDS:]
    new_cursor = max(cursor, now - timedelta(minutes=OVERLAP_MINUTES))
    _save_settings({
        CURSOR_KEY: new_cursor.isoformat(),
        SEEN_IDS_KEY: json.dumps(seen_order),
    })
    return {
        "connected": True,
        "baseline": False,
        "new_emails": len(candidates),
        "new_tasks": len(tasks),
        "scheduled_count": scheduled_count,
    }
