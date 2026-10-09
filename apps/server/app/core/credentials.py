import json
import os
from pathlib import Path
from typing import Optional

from .config import data_directory

CREDENTIALS_FILE_NAME = ".credentials.json"


def _credentials_path() -> Path:
    return data_directory() / CREDENTIALS_FILE_NAME


def _read_credentials() -> dict[str, str]:
    path = _credentials_path()
    if not path.is_file():
        return {}
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return {}


def _write_credentials(data: dict[str, str]) -> None:
    path = _credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write with restricted permissions (0600 - owner read/write only)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with open(fd, "w", encoding="utf-8", closefd=False) as f:
            json.dump(data, f, indent=2)
    finally:
        os.close(fd)


def save_credential(service: str, secret: str) -> None:
    """Securely stores an API key or token outside the database."""
    clean_service = service.strip().lower()
    clean_secret = secret.strip()
    data = _read_credentials()
    data[clean_service] = clean_secret
    _write_credentials(data)


def get_credential(service: str) -> Optional[str]:
    """Retrieves an API key or token without logging."""
    clean_service = service.strip().lower()
    data = _read_credentials()
    return data.get(clean_service)


def delete_credential(service: str) -> bool:
    """Deletes an API key or token."""
    clean_service = service.strip().lower()
    data = _read_credentials()
    if clean_service in data:
        del data[clean_service]
        _write_credentials(data)
        return True
    return False


def has_credential(service: str) -> bool:
    return get_credential(service) is not None


def mask_credential(secret: Optional[str]) -> str:
    """Returns a masked representation, e.g. sk-...1234, never the raw key."""
    if not secret:
        return ""
    if len(secret) <= 8:
        return "••••••••"
    return f"{secret[:3]}...{secret[-4:]}"
