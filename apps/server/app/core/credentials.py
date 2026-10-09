import json
from typing import Optional

import keyring
from keyring.errors import NoKeyringError

from .config import data_directory

KEYRING_SERVICE = "com.leaves.desktop"
LEGACY_CREDENTIALS_FILE = ".credentials.json"


class CredentialStoreUnavailable(RuntimeError):
    """The operating system does not currently expose a secure credential store."""


def _check_keyring() -> None:
    try:
        if keyring.get_keyring().priority <= 0:
            raise NoKeyringError("No secure operating-system credential store is available.")
    except Exception as error:
        raise CredentialStoreUnavailable(
            "Leaves needs an operating-system credential store (Keychain, Credential Manager, or Secret Service)."
        ) from error


def _migrate_legacy_file() -> None:
    """Move credentials from the prototype's private JSON file into the OS store."""
    path = data_directory() / LEGACY_CREDENTIALS_FILE
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or any(not isinstance(v, str) for v in data.values()):
            raise ValueError("Unexpected credential file format")
        for service, secret in data.items():
            account = str(service).strip().lower()
            if keyring.get_password(KEYRING_SERVICE, account) is None:
                keyring.set_password(KEYRING_SERVICE, account, secret)
        path.unlink()
    except Exception as error:
        raise CredentialStoreUnavailable(
            "Could not move existing credentials into the operating-system store; the original file was preserved."
        ) from error


def save_credential(service: str, secret: str) -> None:
    """Store an API key or token using the operating-system credential manager."""
    clean_service = service.strip().lower()
    clean_secret = secret.strip()
    _check_keyring()
    try:
        _migrate_legacy_file()
        keyring.set_password(KEYRING_SERVICE, clean_service, clean_secret)
    except Exception as error:
        if isinstance(error, CredentialStoreUnavailable):
            raise
        raise CredentialStoreUnavailable("Could not save the credential to the operating-system store.") from error


def get_credential(service: str) -> Optional[str]:
    """Retrieve a credential without logging or placing it in SQLite."""
    clean_service = service.strip().lower()
    _check_keyring()
    try:
        _migrate_legacy_file()
        return keyring.get_password(KEYRING_SERVICE, clean_service)
    except Exception as error:
        if isinstance(error, CredentialStoreUnavailable):
            raise
        raise CredentialStoreUnavailable("Could not read the operating-system credential store.") from error


def delete_credential(service: str) -> bool:
    clean_service = service.strip().lower()
    _check_keyring()
    try:
        _migrate_legacy_file()
        if keyring.get_password(KEYRING_SERVICE, clean_service) is None:
            return False
        keyring.delete_password(KEYRING_SERVICE, clean_service)
        return True
    except Exception as error:
        if isinstance(error, CredentialStoreUnavailable):
            raise
        raise CredentialStoreUnavailable("Could not delete the credential from the operating-system store.") from error


def has_credential(service: str) -> bool:
    return get_credential(service) is not None


def mask_credential(secret: Optional[str]) -> str:
    """Return a masked representation, e.g. sk-...1234, never the raw key."""
    if not secret:
        return ""
    if len(secret) <= 8:
        return "••••••••"
    return f"{secret[:3]}...{secret[-4:]}"
