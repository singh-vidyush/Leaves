from contextlib import asynccontextmanager
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.adapters.manager import (
    get_model_settings,
    set_active_provider_name,
)
from app.core.credentials import delete_credential, save_credential
from app.core.database import connect, initialize_database
from app.integrations.gmail.service import (
    delete_email_from_leaves,
    list_emails,
    sync_gmail,
)
from app.integrations.google_calendar.service import (
    add_calendar_event,
    delete_calendar_event,
    list_events,
    move_calendar_event,
    sync_calendar,
)
from app.services.export import export_leaves_data
from app.services.indexing import add_source, refresh_source, remove_source
from app.services.notifications import list_notifications, mark_all_notifications_read, mark_notification_read
from app.services.scheduling import (
    get_availability_settings,
    resolve_conflicts_and_reschedule,
    schedule_task,
    update_availability_settings,
)
from app.services.search import search_documents
from app.services.task_extraction import extract_and_store_tasks, list_tasks, update_task_status


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Leaves Local API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


# --- Request Models ---

class SourceInput(BaseModel):
    path: str
    recursive: bool = True


class ModelSettingsInput(BaseModel):
    active_provider: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None


class AvailabilityInput(BaseModel):
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    default_duration_minutes: Optional[str] = None
    notifications_enabled: Optional[str] = None


class CalendarEventInput(BaseModel):
    title: str
    start_time: str
    end_time: str
    description: Optional[str] = ""


class MoveEventInput(BaseModel):
    start_time: str
    end_time: str


class TaskStatusInput(BaseModel):
    status: str


# --- Core Endpoints ---

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "leaves-local"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    with connect() as db:
        source_count = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        document_count = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        email_count = db.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        calendar_count = db.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0]
        pending_task_count = db.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
        unread_notifications = db.execute("SELECT COUNT(*) FROM notifications WHERE is_read=0").fetchone()[0]

        sources = [dict(row) for row in db.execute(
            "SELECT id, path, recursive, created_at, last_indexed_at FROM sources ORDER BY created_at DESC"
        ).fetchall()]
        recent_docs = [dict(row) for row in db.execute(
            "SELECT title, path, modified_at FROM documents ORDER BY modified_at DESC LIMIT 5"
        ).fetchall()]
        upcoming_events = [dict(row) for row in db.execute(
            "SELECT id, title, start_time, end_time, created_by FROM calendar_events ORDER BY start_time ASC LIMIT 5"
        ).fetchall()]
        high_priority_tasks = [dict(row) for row in db.execute(
            "SELECT id, title, urgency_score, urgency_reason, deadline, status FROM tasks WHERE status='pending' ORDER BY urgency_score DESC LIMIT 5"
        ).fetchall()]

    return {
        "source_count": source_count,
        "document_count": document_count,
        "email_count": email_count,
        "calendar_count": calendar_count,
        "pending_task_count": pending_task_count,
        "unread_notifications": unread_notifications,
        "sources": sources,
        "recent_documents": recent_docs,
        "upcoming_events": upcoming_events,
        "high_priority_tasks": high_priority_tasks,
    }


# --- Source Management ---

@app.get("/api/sources")
def list_sources() -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT id, path, recursive, created_at, last_indexed_at FROM sources ORDER BY created_at DESC"
        ).fetchall()]


@app.post("/api/sources")
def create_source(payload: SourceInput) -> dict:
    try:
        return add_source(payload.path, payload.recursive)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=400, detail="Could not read the selected folder.") from error


@app.post("/api/sources/{source_id}/refresh")
def refresh(source_id: int) -> dict:
    try:
        return refresh_source(source_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: int) -> dict:
    if not remove_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"deleted": True, "original_files_deleted": False}


# --- Full-Text Search ---

@app.get("/api/search")
def search(q: str = Query(default="", max_length=300), limit: int = Query(default=30, ge=1, le=100)) -> list[dict]:
    try:
        return search_documents(q, limit)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Search could not be completed.") from error


# --- Settings & Model Providers ---

@app.get("/api/settings/model")
def get_model_config() -> dict:
    return get_model_settings()


@app.post("/api/settings/model")
def update_model_config(payload: ModelSettingsInput) -> dict:
    if payload.active_provider:
        try:
            set_active_provider_name(payload.active_provider)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

    if payload.provider and payload.api_key:
        save_credential(payload.provider, payload.api_key)

    return get_model_settings()


@app.delete("/api/settings/model/{provider}")
def delete_model_key(provider: str) -> dict:
    deleted = delete_credential(provider)
    return {"deleted": deleted, "provider": provider}


@app.get("/api/settings/availability")
def get_availability() -> dict:
    return get_availability_settings()


@app.post("/api/settings/availability")
def update_availability(payload: AvailabilityInput) -> dict:
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    return update_availability_settings(data)


# --- Gmail Integration ---

@app.post("/api/integrations/gmail/sync")
def sync_gmail_endpoint(label: Optional[str] = None) -> dict:
    return sync_gmail(filter_label=label)


@app.get("/api/integrations/gmail/emails")
def list_gmail_emails(limit: int = 50, label: Optional[str] = None) -> list[dict]:
    return list_emails(limit=limit, label=label)


@app.delete("/api/integrations/gmail/emails/{email_id}")
def delete_email_endpoint(email_id: int) -> dict:
    deleted = delete_email_from_leaves(email_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Email not found in Leaves.")
    return {"deleted": True, "original_email_deleted": False}


# --- Google Calendar Integration ---

@app.post("/api/integrations/calendar/sync")
def sync_calendar_endpoint() -> dict:
    return sync_calendar()


@app.get("/api/integrations/calendar/events")
def list_calendar_events_endpoint(limit: int = 50) -> list[dict]:
    return list_events(limit=limit)


@app.post("/api/integrations/calendar/events")
def add_calendar_event_endpoint(payload: CalendarEventInput) -> dict:
    return add_calendar_event(
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        description=payload.description or "",
    )


@app.put("/api/integrations/calendar/events/{event_id}")
def move_calendar_event_endpoint(event_id: int, payload: MoveEventInput) -> dict:
    try:
        return move_calendar_event(event_id, payload.start_time, payload.end_time)
    except LookupError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@app.delete("/api/integrations/calendar/events/{event_id}")
def delete_calendar_event_endpoint(
    event_id: int,
    confirmed: bool = Query(default=False, description="Explicit user confirmation required"),
) -> dict:
    """
    CRITICAL: Calendar deletion always requires explicit user approval.
    """
    if not confirmed:
        raise HTTPException(
            status_code=400,
            detail="Deleting calendar events always requires explicit user confirmation. Pass confirmed=true.",
        )
    deleted = delete_calendar_event(event_id, user_confirmed=True)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found.")
    return {"deleted": True, "original_event_deleted": False}


# --- Tasks & Scheduling ---

@app.post("/api/tasks/extract")
def extract_tasks_endpoint() -> list[dict]:
    return extract_and_store_tasks()


@app.get("/api/tasks")
def list_tasks_endpoint(status: Optional[str] = None) -> list[dict]:
    return list_tasks(status=status)


@app.post("/api/tasks/{task_id}/schedule")
def schedule_task_endpoint(task_id: int) -> dict:
    try:
        return schedule_task(task_id)
    except LookupError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@app.put("/api/tasks/{task_id}/status")
def update_task_status_endpoint(task_id: int, payload: TaskStatusInput) -> dict:
    try:
        return update_task_status(task_id, payload.status)
    except LookupError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@app.post("/api/schedule/resolve-conflicts")
def resolve_conflicts_endpoint() -> list[dict]:
    return resolve_conflicts_and_reschedule()


# --- Notifications ---

@app.get("/api/notifications")
def list_notifications_endpoint(unread_only: bool = False, limit: int = 50) -> list[dict]:
    return list_notifications(unread_only=unread_only, limit=limit)


@app.post("/api/notifications/{notification_id}/read")
def read_notification_endpoint(notification_id: int) -> dict:
    success = mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"read": True}


@app.post("/api/notifications/read-all")
def read_all_notifications_endpoint() -> dict:
    count = mark_all_notifications_read()
    return {"marked_read": count}


# --- Data Export ---

@app.get("/api/export")
def export_data_endpoint() -> dict:
    return export_leaves_data()
