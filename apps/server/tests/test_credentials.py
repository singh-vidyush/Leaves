import pytest

from app.core import credentials
from app.core.credentials import CredentialStoreUnavailable, get_credential, save_credential


def test_legacy_credentials_are_migrated_to_keyring(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))
    legacy_file = tmp_path / ".credentials.json"
    legacy_file.write_text('{"openai":"example-secret"}', encoding="utf-8")

    assert get_credential("openai") == "example-secret"
    assert not legacy_file.exists()


def test_credentials_are_read_from_keyring(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAVES_DATA_DIR", str(tmp_path))

    save_credential("anthropic", "test-key")

    assert get_credential("anthropic") == "test-key"
    assert not (tmp_path / ".credentials.json").exists()


def test_unavailable_secure_store_fails_closed(monkeypatch):
    unavailable = type("UnavailableKeyring", (), {"priority": 0})()
    monkeypatch.setattr(credentials.keyring, "get_keyring", lambda: unavailable)

    with pytest.raises(CredentialStoreUnavailable):
        save_credential("openai", "test-key")
