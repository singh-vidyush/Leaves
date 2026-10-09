from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_google_oauth_credentials_can_be_saved_and_removed_without_echoing_values():
    client_id = "1234567890-client.apps.googleusercontent.com"
    client_secret = "never-return-this-secret"

    saved = client.put(
        "/api/settings/google-oauth",
        json={"client_id": client_id, "client_secret": client_secret},
    )

    assert saved.status_code == 200
    assert saved.json() == {
        "client_id_configured": True,
        "client_secret_configured": True,
        "ready": True,
    }
    assert client_secret not in saved.text
    assert client_id not in saved.text

    status = client.get("/api/settings/google-oauth")
    assert status.status_code == 200
    assert status.json() == saved.json()
    assert client_secret not in status.text
    assert client_id not in status.text

    removed = client.delete("/api/settings/google-oauth")
    assert removed.status_code == 200
    assert removed.json()["ready"] is False


def test_google_oauth_endpoint_returns_clear_validation_error():
    response = client.put("/api/settings/google-oauth", json={"client_id": "bad-id"})

    assert response.status_code == 400
    assert "Google OAuth Desktop client" in response.json()["detail"]
