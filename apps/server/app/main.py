from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator

from app.adapters.manager import (
    get_model_settings,
    set_active_provider_name,
)
from app.core.credentials import CredentialStoreUnavailable, delete_credential, save_credential
from app.core.database import connect, initialize_database
from app.integrations.gmail.service import (
    delete_email_from_leaves,
    list_emails,
    sync_gmail,
)
from app.integrations.connectors import get_schedule_connector, get_schedule_connectors
from app.integrations.google_oauth import (
    GoogleOAuthError,
    begin_google_oauth,
    complete_google_oauth,
    disconnect_google_service,
    google_connection_status,
)
from app.integrations.google_calendar.service import calendar_is_connected, get_event as get_calendar_event
from app.services.export import export_leaves_data
from app.services.indexing import add_source, refresh_source, remove_source
from app.services.notifications import list_notifications, mark_all_notifications_read, mark_notification_read
from app.services.scheduling import (
    get_availability_settings,
    add_time_away_block,
    list_time_away_blocks,
    remove_time_away_block,
    NoAvailableSlotError,
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


class TimeAwayInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    start_time: datetime
    end_time: datetime

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Time-away title cannot be blank.")
        return clean

    @model_validator(mode="after")
    def validate_range(self):
        if self.start_time.tzinfo is None or self.end_time.tzinfo is None:
            raise ValueError("Time-away dates must include a timezone.")
        if self.end_time <= self.start_time:
            raise ValueError("Time-away end must be later than its start.")
        return self


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
    try:
        return get_model_settings()
    except CredentialStoreUnavailable as err:
        raise HTTPException(status_code=503, detail=str(err)) from err


@app.post("/api/settings/model")
def update_model_config(payload: ModelSettingsInput) -> dict:
    if payload.active_provider:
        try:
            set_active_provider_name(payload.active_provider)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

    if payload.provider and payload.api_key:
        try:
            save_credential(payload.provider, payload.api_key)
        except CredentialStoreUnavailable as err:
            raise HTTPException(status_code=503, detail=str(err)) from err

    try:
        return get_model_settings()
    except CredentialStoreUnavailable as err:
        raise HTTPException(status_code=503, detail=str(err)) from err


@app.delete("/api/settings/model/{provider}")
def delete_model_key(provider: str) -> dict:
    try:
        deleted = delete_credential(provider)
    except CredentialStoreUnavailable as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    return {"deleted": deleted, "provider": provider}


@app.get("/api/settings/availability")
def get_availability() -> dict:
    return get_availability_settings()


@app.post("/api/settings/availability")
def update_availability(payload: AvailabilityInput) -> dict:
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    return update_availability_settings(data)


@app.get("/api/settings/time-away")
def get_time_away_blocks() -> list[dict]:
    return list_time_away_blocks()


@app.post("/api/settings/time-away")
def create_time_away_block(payload: TimeAwayInput) -> dict:
    return add_time_away_block(
        payload.title,
        payload.start_time.isoformat(),
        payload.end_time.isoformat(),
    )


@app.delete("/api/settings/time-away/{block_id}")
def delete_time_away_block(block_id: int) -> dict:
    if not remove_time_away_block(block_id):
        raise HTTPException(status_code=404, detail="Time-away block not found.")
    return {"deleted": True}


# --- Gmail Integration ---

@app.post("/api/integrations/gmail/sync")
def sync_gmail_endpoint(label: Optional[str] = None) -> dict:
    try:
        return sync_gmail(filter_label=label)
    except CredentialStoreUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/auth/google/status")
def google_status_endpoint() -> dict[str, bool]:
    try:
        return google_connection_status()
    except CredentialStoreUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/auth/google/{service}/start")
def google_oauth_start_endpoint(service: str) -> dict[str, str]:
    try:
        return begin_google_oauth(service)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except GoogleOAuthError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.delete("/api/auth/google/{service}")
def google_disconnect_endpoint(service: str) -> dict[str, bool]:
    try:
        return {"disconnected": disconnect_google_service(service)}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except CredentialStoreUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/auth/google/callback", response_class=HTMLResponse)
def google_oauth_callback_endpoint(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        return HTMLResponse("<h2>Google connection was not completed.</h2><p>You can close this tab and return to Leaves.</p>", status_code=400)
    if not code or not state:
        raise HTTPException(status_code=400, detail="Google authorization callback is missing its code or state.")
    try:
        service = complete_google_oauth(state, code)
    except GoogleOAuthError as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception
    except CredentialStoreUnavailable as exception:
        raise HTTPException(status_code=503, detail=str(exception)) from exception
    return HTMLResponse(f"<h2>Google {service.title()} connected to Leaves.</h2><p>You can close this tab and return to Leaves.</p>")


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

@app.get("/api/integrations/schedule-connectors")
def list_schedule_connectors_endpoint() -> list[dict]:
    try:
        return [
        {
            "id": connector.id,
            "display_name": connector.display_name,
            "live": connector.is_live,
            "capabilities": ["read", "create", "move", "delete-with-confirmation"],
        }
            for connector in get_schedule_connectors()
        ]
    except CredentialStoreUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

@app.post("/api/integrations/calendar/sync")
def sync_calendar_endpoint() -> dict:
    try:
        return get_schedule_connector("local_calendar").sync()
    except CredentialStoreUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/integrations/calendar/events")
def list_calendar_events_endpoint(limit: int = 50) -> list[dict]:
    return get_schedule_connector("local_calendar").list_events(limit=limit)


@app.post("/api/integrations/calendar/events")
def add_calendar_event_endpoint(payload: CalendarEventInput) -> dict:
    return get_schedule_connector("local_calendar").add_event(
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        description=payload.description or "",
    )


@app.put("/api/integrations/calendar/events/{event_id}")
def move_calendar_event_endpoint(event_id: int, payload: MoveEventInput) -> dict:
    try:
        return get_schedule_connector("local_calendar").move_event(event_id, payload.start_time, payload.end_time)
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
    event = get_calendar_event(event_id)
    deleted_remote = bool(
        event
        and event.get("remote_id")
        and event.get("created_by") == "leaves"
        and calendar_is_connected()
    )
    deleted = get_schedule_connector("local_calendar").delete_event(event_id, user_confirmed=True)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found.")
    return {"deleted": True, "original_event_deleted": deleted_remote}


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
    except NoAvailableSlotError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err


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
