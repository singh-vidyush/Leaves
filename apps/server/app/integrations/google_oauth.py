"""Installed-app Google OAuth using PKCE and OS-backed credential storage."""

from dataclasses import dataclass
import base64
import hashlib
import json
import os
import secrets
import threading
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.credentials import CredentialStoreUnavailable, delete_credential, get_credential, save_credential

SCOPES = {
    "gmail": "https://www.googleapis.com/auth/gmail.readonly",
    "calendar": "https://www.googleapis.com/auth/calendar.events.owned",
}
GOOGLE_CLIENT_ID_ENV = "GOOGLE_OAUTH_CLIENT_ID"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
TOKEN_SERVICE_PREFIX = "google_oauth_"
OAUTH_STATE_TTL_SECONDS = 600


class GoogleOAuthError(RuntimeError):
    pass


@dataclass
class OAuthTransaction:
    service: str
    code_verifier: str
    redirect_uri: str
    expires_at: float


_transactions: dict[str, OAuthTransaction] = {}
_transactions_lock = threading.Lock()


def _client_id() -> str:
    client_id = os.environ.get(GOOGLE_CLIENT_ID_ENV, "").strip()
    if not client_id:
        raise GoogleOAuthError(
            f"Set {GOOGLE_CLIENT_ID_ENV} to a Google OAuth desktop client ID before connecting an account."
        )
    return client_id


def begin_google_oauth(service: str) -> dict[str, str]:
    if service not in SCOPES:
        raise ValueError("Google service must be 'gmail' or 'calendar'.")
    client_id = _client_id()
    port = int(os.environ.get("LEAVES_API_PORT", "8000"))
    redirect_uri = f"http://127.0.0.1:{port}/api/auth/google/callback"
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    state = secrets.token_urlsafe(32)
    with _transactions_lock:
        now = time.time()
        for old_state, transaction in list(_transactions.items()):
            if transaction.expires_at <= now:
                _transactions.pop(old_state, None)
        _transactions[state] = OAuthTransaction(
            service=service,
            code_verifier=verifier,
            redirect_uri=redirect_uri,
            expires_at=now + OAUTH_STATE_TTL_SECONDS,
        )
    query = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES[service],
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    })
    return {"authorization_url": f"{GOOGLE_AUTH_URL}?{query}", "state": state, "service": service}


def complete_google_oauth(state: str, code: str) -> str:
    with _transactions_lock:
        transaction = _transactions.pop(state, None)
    if transaction is None or transaction.expires_at <= time.time():
        raise GoogleOAuthError("This Google authorization expired or was already used. Start the connection again.")

    try:
        response = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": _client_id(),
                "code": code,
                "code_verifier": transaction.code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": transaction.redirect_uri,
            },
            timeout=20.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            google_error = payload.get("error") if isinstance(payload, dict) else None
            google_description = payload.get("error_description") if isinstance(payload, dict) else None
            if not isinstance(google_description, str):
                google_description = None
            elif len(google_description) > 300:
                google_description = google_description[:300]
            if google_error == "invalid_client":
                detail = "Google rejected the OAuth client ID. Check that the local value is a Desktop client ID from the configured project."
            elif google_error == "invalid_grant":
                detail = "Google rejected or expired the authorization code. Start a new sign-in; if this repeats, check that the same Desktop client is used throughout OAuth."
            elif google_error == "redirect_uri_mismatch":
                detail = "Google rejected the callback URL. Check the OAuth client type and loopback redirect configuration."
            else:
                detail = f"Google token exchange failed ({google_error or response.status_code})."
            if google_description:
                detail = f"{detail} Google says: {google_description}"
            raise GoogleOAuthError(detail) from error
        token = response.json()
        access_token = token["access_token"]
        previous = get_credential(f"{TOKEN_SERVICE_PREFIX}{transaction.service}")
        previous_token = json.loads(previous) if previous else {}
        refresh_token = token.get("refresh_token") or previous_token.get("refresh_token")
        if not refresh_token:
            raise GoogleOAuthError("Google did not return an offline refresh token. Reconnect and approve offline access.")
        stored = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": int(time.time()) + int(token.get("expires_in", 3600)),
            "scope": token.get("scope", SCOPES[transaction.service]),
        }
        save_credential(f"{TOKEN_SERVICE_PREFIX}{transaction.service}", json.dumps(stored))
    except (GoogleOAuthError, CredentialStoreUnavailable):
        raise
    except Exception as error:
        raise GoogleOAuthError("Google authorization could not be completed. Check the OAuth client and try again.") from error
    return transaction.service


def get_google_access_token(service: str) -> str:
    if service not in SCOPES:
        raise ValueError("Google service must be 'gmail' or 'calendar'.")
    raw = get_credential(f"{TOKEN_SERVICE_PREFIX}{service}")
    if not raw:
        raise GoogleOAuthError(f"Connect Google {service.title()} before syncing.")
    try:
        token: dict[str, Any] = json.loads(raw)
        if token.get("access_token") and int(token.get("expires_at", 0)) > int(time.time()) + 60:
            return str(token["access_token"])
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise GoogleOAuthError("Google authorization expired. Reconnect this account.")
        response = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": _client_id(),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=20.0,
        )
        response.raise_for_status()
        refreshed = response.json()
        token["access_token"] = refreshed["access_token"]
        token["expires_at"] = int(time.time()) + int(refreshed.get("expires_in", 3600))
        if refreshed.get("scope"):
            token["scope"] = refreshed["scope"]
        save_credential(f"{TOKEN_SERVICE_PREFIX}{service}", json.dumps(token))
        return str(token["access_token"])
    except GoogleOAuthError:
        raise
    except Exception as error:
        raise GoogleOAuthError(f"Google {service.title()} authorization expired or could not refresh. Reconnect the account.") from error


def google_connection_status() -> dict[str, bool]:
    return {
        service: get_credential(f"{TOKEN_SERVICE_PREFIX}{service}") is not None
        for service in SCOPES
    }


def google_service_connected(service: str) -> bool:
    if service not in SCOPES:
        raise ValueError("Google service must be 'gmail' or 'calendar'.")
    return get_credential(f"{TOKEN_SERVICE_PREFIX}{service}") is not None


def disconnect_google_service(service: str) -> bool:
    if service not in SCOPES:
        raise ValueError("Google service must be 'gmail' or 'calendar'.")
    key = f"{TOKEN_SERVICE_PREFIX}{service}"
    raw = get_credential(key)
    if not raw:
        return False
    token = json.loads(raw)
    refresh_token = token.get("refresh_token")
    if refresh_token:
        try:
            httpx.post(GOOGLE_REVOKE_URL, data={"token": refresh_token}, timeout=20.0)
        except httpx.HTTPError:
            # Local disconnect must remain available when Google's revocation API
            # is unreachable; deleting the local refresh token prevents reuse.
            pass
    return delete_credential(key)
