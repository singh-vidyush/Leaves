import keyring
import pytest


@pytest.fixture(autouse=True)
def in_memory_credential_store(monkeypatch):
    credentials = {}
    backend = type("TestKeyring", (), {"priority": 1})()
    monkeypatch.setattr(keyring, "get_keyring", lambda: backend)
    monkeypatch.setattr(keyring, "get_password", lambda service, username: credentials.get((service, username)))
    monkeypatch.setattr(
        keyring,
        "set_password",
        lambda service, username, password: credentials.__setitem__((service, username), password),
    )

    def delete_password(service, username):
        credentials.pop((service, username), None)

    monkeypatch.setattr(keyring, "delete_password", delete_password)
