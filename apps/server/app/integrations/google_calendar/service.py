from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from app.core.database import connect
from app.integrations.google_oauth import get_google_access_token, google_service_connected

GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

SAMPLE_CALENDAR_EVENTS = [
    {"remote_id": "cal-sample-001", "title": "Weekly Team Standup", "description": "Weekly engineering check-in", "start_offset_hours": 1, "duration_minutes": 30, "created_by": "external"},
    {"remote_id": "cal-sample-002", "title": "Architecture Sync with Product", "description": "Review sprint objectives and integrations", "start_offset_hours": 4, "duration_minutes": 60, "created_by": "external"},
]


def calendar_is_connected() -> bool:
    return google_service_connected("calendar")


def _google_request(method: str, path: str = "", **kwargs: Any) -> dict[str, Any]:
    token = get_google_access_token("calendar")
    url = f"{GOOGLE_CALENDAR_API}{path}"
    headers = {"Authorization": f"Bearer {token}", **kwargs.pop("headers", {})}
    try:
        response = httpx.request(method, url, headers=headers, timeout=30.0, **kwargs)
        if response.is_error:
            raise RuntimeError("Google Calendar request failed. Check the granted permission and reconnect.")
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()
    except httpx.HTTPError as error:
        raise RuntimeError("Google Calendar could not be reached. Try syncing again.") from error


def _event_times(item: dict[str, Any]) -> tuple[str, str]:
    start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
    end = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
    if not start or not end:
        raise RuntimeError("Google Calendar returned an event without a usable time range.")
    if len(start) == 10:
        start += "T00:00:00+00:00"
    if len(end) == 10:
        end += "T00:00:00+00:00"
    return start, end


def _upsert_google_event(item: dict[str, Any]) -> int:
    remote_id = item["id"]
    if item.get("status") == "cancelled":
        with connect() as db:
            existing = db.execute("SELECT id FROM calendar_events WHERE remote_id=?", (remote_id,)).fetchone()
            if not existing:
                return 0
            db.execute(
                "UPDATE calendar_events SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (existing["id"],),
            )
            return int(existing["id"])
    start, end = _event_times(item)
    title = item.get("summary") or "(no title)"
    description = item.get("description") or ""
    with connect() as db:
        existing = db.execute("SELECT id FROM calendar_events WHERE remote_id=?", (remote_id,)).fetchone()
        if existing:
            db.execute("UPDATE calendar_events SET title=?, description=?, start_time=?, end_time=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                       (title, description, start, end, "cancelled" if item.get("status") == "cancelled" else "confirmed", existing["id"]))
            return int(existing["id"])
        cursor = db.execute("INSERT INTO calendar_events(remote_id, title, description, start_time, end_time, status, created_by) VALUES (?, ?, ?, ?, ?, ?, 'external')",
                            (remote_id, title, description, start, end, "cancelled" if item.get("status") == "cancelled" else "confirmed"))
        return int(cursor.lastrowid)


def sync_calendar() -> dict[str, Any]:
    if not calendar_is_connected():
        now = datetime.now(timezone.utc)
        count = 0
        with connect() as db:
            for sample in SAMPLE_CALENDAR_EVENTS:
                start = (now + timedelta(hours=sample["start_offset_hours"])).isoformat()
                end = (now + timedelta(hours=sample["start_offset_hours"], minutes=sample["duration_minutes"])).isoformat()
                exists = db.execute("SELECT id FROM calendar_events WHERE remote_id=?", (sample["remote_id"],)).fetchone()
                if not exists:
                    db.execute("INSERT INTO calendar_events(remote_id, title, description, start_time, end_time, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                               (sample["remote_id"], sample["title"], sample["description"], start, end, sample["created_by"]))
                    count += 1
        return {"synced_count": count, "mode": "sample"}

    get_google_access_token("calendar")
    params = {
        "timeMin": datetime.now(timezone.utc).isoformat(),
        "singleEvents": "true",
        "showDeleted": "true",
        "orderBy": "startTime",
        "maxResults": 2500,
    }
    count = 0
    while True:
        page = _google_request("GET", params=params)
        for item in page.get("items", []):
            if _upsert_google_event(item):
                count += 1
        token = page.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    return {"synced_count": count, "mode": "live"}


def list_events(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, remote_id, title, description, start_time, end_time, status, created_by, created_at, updated_at "
            "FROM calendar_events WHERE status != 'cancelled' ORDER BY start_time ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_event(event_id: int) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None


def _google_event(title: str, start_time: str, end_time: str, description: str) -> dict[str, Any]:
    return {"summary": title, "description": description, "start": {"dateTime": start_time}, "end": {"dateTime": end_time}}


def add_calendar_event(title: str, start_time: str, end_time: str, description: str = "", created_by: str = "leaves") -> dict[str, Any]:
    remote_id = None
    if calendar_is_connected():
        remote_id = _google_request("POST", json=_google_event(title, start_time, end_time, description)).get("id")
    with connect() as db:
        cursor = db.execute("INSERT INTO calendar_events(remote_id, title, description, start_time, end_time, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (remote_id, title, description, start_time, end_time, created_by))
        return dict(db.execute("SELECT * FROM calendar_events WHERE id=?", (cursor.lastrowid,)).fetchone())


def move_calendar_event(event_id: int, new_start_time: str, new_end_time: str) -> dict[str, Any]:
    event = get_event(event_id)
    if not event:
        raise LookupError(f"Event {event_id} not found.")
    if event["remote_id"] and event["created_by"] == "leaves" and calendar_is_connected():
        _google_request("PUT", f"/{event['remote_id']}", json=_google_event(event["title"], new_start_time, new_end_time, event["description"]))
    with connect() as db:
        db.execute("UPDATE calendar_events SET start_time=?, end_time=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_start_time, new_end_time, event_id))
        return dict(db.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone())


def delete_calendar_event(event_id: int, user_confirmed: bool = False) -> bool:
    if not user_confirmed:
        raise PermissionError("Deleting calendar events always requires explicit user approval.")
    event = get_event(event_id)
    if not event:
        return False
    if event["remote_id"] and event["created_by"] == "leaves" and calendar_is_connected():
        _google_request("DELETE", f"/{event['remote_id']}")
    with connect() as db:
        return db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,)).rowcount > 0
