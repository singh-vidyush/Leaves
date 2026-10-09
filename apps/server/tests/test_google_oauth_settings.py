import json

import pytest

from app.integrations import google_oauth


def test_google_oauth_settings_store_only_presence_and_mask_no_values(monkeypatch):
    store = {}
    monkeypatch.setattr(google_oauth, "get_credential", lambda name: store.get(name))
    monkeypatch.setattr(google_oauth, "save_credential", lambda name, value: store.__setitem__(name, value))

    status = google_oauth.save_google_oauth_settings(
        "1234567890-client.apps.googleusercontent.com",
        "very-secret-oauth-value",
    )

    assert status == {
        "client_id_configured": True,
        "client_secret_configured": True,
        "ready": True,
    }
    assert "very-secret-oauth-value" not in json.dumps(status)
    assert "1234567890-client.apps.googleusercontent.com" not in json.dumps(status)


@pytest.mark.parametrize(
    ("client_id", "client_secret", "message"),
    [
        ("not-a-google-client-id", None, "Google OAuth Desktop client"),
        (None, "short", "at least 8 characters"),
        (None, None, "Enter a Client ID or Client Secret"),
    ],
)
def test_google_oauth_settings_validation(client_id, client_secret, message):
    with pytest.raises(ValueError, match=message):
        google_oauth.save_google_oauth_settings(client_id, client_secret)


def test_remove_google_oauth_settings_deletes_tokens_and_client_values(monkeypatch):
    store = {
        google_oauth.GOOGLE_CLIENT_ID_CREDENTIAL: "client-id",
        google_oauth.GOOGLE_CLIENT_SECRET_CREDENTIAL: "client-secret",
    }
    disconnected = []
    monkeypatch.setattr(google_oauth, "get_credential", lambda name: store.get(name))
    monkeypatch.setattr(google_oauth, "delete_credential", lambda name: store.pop(name, None) is not None)
    monkeypatch.setattr(google_oauth, "disconnect_google_service", disconnected.append)

    status = google_oauth.remove_google_oauth_settings()

    assert disconnected == ["gmail", "calendar"]
    assert store == {}
    assert status == {
        "client_id_configured": False,
        "client_secret_configured": False,
        "ready": False,
    }
