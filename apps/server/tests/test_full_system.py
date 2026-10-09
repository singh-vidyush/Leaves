import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import connect
from app.services.scheduling import (
    find_next_available_slot,
    schedule_task,
    update_availability_settings,
)

client = TestClient(app)


def test_dashboard_full_stats(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "source_count" in data
    assert "email_count" in data
    assert "calendar_count" in data
    assert "pending_task_count" in data
    assert "unread_notifications" in data
    assert "high_priority_tasks" in data


def test_model_and_availability_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))

    # Initial model settings
    res = client.get("/api/settings/model")
    assert res.status_code == 200
    assert "active_provider" in res.json()

    # Configure API key
    res = client.post("/api/settings/model", json={"provider": "openai", "api_key": "sk-secret-key-12345"})
    assert res.status_code == 200
    providers = res.json()["providers"]
    assert providers["openai"]["configured"] is True
    # Verify raw secret is NEVER exposed
    assert "sk-secret-key-12345" not in str(res.json())

    # Switch active provider
    res = client.post("/api/settings/model", json={"active_provider": "openai"})
    assert res.status_code == 200
    assert res.json()["active_provider"] == "openai"

    # Availability settings
    res = client.get("/api/settings/availability")
    assert res.status_code == 200
    assert res.json()["working_hours_start"] == "09:00"

    res = client.post("/api/settings/availability", json={"working_hours_start": "08:30", "break_start": "12:30"})
    assert res.status_code == 200
    assert res.json()["working_hours_start"] == "08:30"
    assert res.json()["break_start"] == "12:30"


def test_gmail_integration_and_deletion_safeguard(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))

    # Sync emails
    res = client.post("/api/integrations/gmail/sync")
    assert res.status_code == 200
    assert res.json()["synced_count"] >= 2

    # List emails
    res = client.get("/api/integrations/gmail/emails")
    assert res.status_code == 200
    emails = res.json()
    assert len(emails) >= 2
    target_id = emails[0]["id"]

    # Delete email from Leaves only
    res = client.delete(f"/api/integrations/gmail/emails/{target_id}")
    assert res.status_code == 200
    assert res.json()["deleted"] is True
    assert res.json()["original_email_deleted"] is False


def test_calendar_integration_and_deletion_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))

    # Add an event
    now = datetime.now(timezone.utc)
    start = (now + timedelta(hours=2)).isoformat()
    end = (now + timedelta(hours=3)).isoformat()

    res = client.post("/api/integrations/calendar/events", json={
        "title": "Strategy Sync",
        "start_time": start,
        "end_time": end,
        "description": "Discuss Q4 objectives",
    })
    assert res.status_code == 200
    event_id = res.json()["id"]

    # Move event
    new_start = (now + timedelta(hours=3)).isoformat()
    new_end = (now + timedelta(hours=4)).isoformat()
    res = client.put(f"/api/integrations/calendar/events/{event_id}", json={
        "start_time": new_start,
        "end_time": new_end,
    })
    assert res.status_code == 200
    assert res.json()["start_time"] == new_start

    # NON-NEGOTIABLE: Attempting to delete calendar event without user approval MUST fail!
    res = client.delete(f"/api/integrations/calendar/events/{event_id}")
    assert res.status_code == 400
    assert "explicit user confirmation" in res.json()["detail"]

    # Deleting with explicit approval succeeds
    res = client.delete(f"/api/integrations/calendar/events/{event_id}?confirmed=true")
    assert res.status_code == 200
    assert res.json()["deleted"] is True


def test_task_extraction_and_scheduling(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))

    # Sync emails so there is context
    client.post("/api/integrations/gmail/sync")

    # Extract tasks
    res = client.post("/api/tasks/extract")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) > 0

    # Verify explainable urgency
    first_task = tasks[0]
    assert "urgency_score" in first_task
    assert "urgency_reason" in first_task
    assert first_task["status"] == "pending"

    # Schedule the task
    res = client.post(f"/api/tasks/{first_task['id']}/schedule")
    assert res.status_code == 200
    assert "event" in res.json()

    # Verify task status is scheduled
    res = client.get("/api/tasks")
    scheduled_tasks = [t for t in res.json() if t["id"] == first_task["id"]]
    assert scheduled_tasks[0]["status"] == "scheduled"

    # Verify notification created
    res = client.get("/api/notifications")
    assert res.status_code == 200
    notifs = res.json()
    assert len(notifs) > 0
    assert "Scheduled" in notifs[0]["title"]


def test_export_leaves_data(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    res = client.get("/api/export")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0"
    assert "sources" in data
    assert "emails" in data
    assert "calendar_events" in data
    assert "time_away_blocks" in data
    assert "tasks" in data
    assert "notifications" in data


def test_time_away_block_is_respected(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    now = datetime.now(timezone.utc)
    days_until_monday = (7 - now.weekday()) % 7
    target_monday = (now + timedelta(days=days_until_monday + 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    away_start = target_monday.replace(hour=9)
    away_end = target_monday.replace(hour=10)
    response = client.post("/api/settings/time-away", json={
        "title": "Appointment",
        "start_time": away_start.isoformat(),
        "end_time": away_end.isoformat(),
    })
    assert response.status_code == 200

    slot_start, slot_end = find_next_available_slot(30, target_monday)

    assert slot_start >= away_end
    assert slot_end > slot_start


def test_notification_preference_disables_schedule_notifications(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    update_availability_settings({"notifications_enabled": "false"})
    with connect() as db:
        task_id = db.execute(
            "INSERT INTO tasks(title, source_type, source_ref, suggested_duration_minutes) VALUES (?, ?, ?, ?)",
            ("Write project plan", "markdown", "notes.md", 30),
        ).lastrowid

    schedule_task(task_id)

    with connect() as db:
        count = db.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    assert count == 0
