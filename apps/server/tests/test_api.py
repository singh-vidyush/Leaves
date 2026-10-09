import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import credentials

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "leaves-local"

def test_dashboard():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "source_count" in data
    assert "document_count" in data
    assert "sources" in data
    assert "recent_documents" in data


def test_schedule_connector_registry():
    response = client.get("/api/integrations/schedule-connectors")
    assert response.status_code == 200
    connectors = response.json()
    assert connectors == [{
        "id": "local_calendar",
        "display_name": "Local Calendar",
        "live": False,
        "capabilities": ["read", "create", "move", "delete-with-confirmation"],
    }]


def test_model_settings_reports_unavailable_credential_store(monkeypatch):
    unavailable = type("UnavailableKeyring", (), {"priority": 0})()
    monkeypatch.setattr(credentials.keyring, "get_keyring", lambda: unavailable)

    response = client.get("/api/settings/model")

    assert response.status_code == 503
    assert "operating-system credential store" in response.json()["detail"]
