from datetime import datetime, timedelta, timezone
import base64
from html.parser import HTMLParser
import json
from typing import Any, Optional

import httpx

from app.core.database import connect
from app.core.credentials import CredentialStoreUnavailable
from app.integrations.google_oauth import GoogleOAuthError, get_google_access_token, google_service_connected

SAMPLE_GMAIL_MESSAGES = [
    {
        "remote_id": "msg-sample-001",
        "subject": "Urgent: Review Q3 product roadmap before Thursday",
        "sender": "sarah.pm@example.com",
        "recipient": "me@example.com",
        "snippet": "Please review the updated roadmap document and leave comments before Thursday noon.",
        "body": "Hi team,\n\nPlease review the updated roadmap document and leave comments before Thursday noon. This is blocking our release planning.\n\nThanks,\nSarah",
        "labels": ["INBOX", "Work", "Urgent"],
        "date": datetime.now(timezone.utc).isoformat(),
    },
    {
        "remote_id": "msg-sample-002",
        "subject": "Follow up with client regarding API migration contract",
        "sender": "david.director@example.com",
        "recipient": "me@example.com",
        "snippet": "We need to follow up with Acme Corp about their contract renewal by tomorrow.",
        "body": "Hello,\n\nWe need to follow up with Acme Corp about their contract renewal by tomorrow. Let me know if you need any numbers.\n\nBest,\nDavid",
        "labels": ["INBOX", "Clients"],
        "date": datetime.now(timezone.utc).isoformat(),
    },
    {
        "remote_id": "msg-sample-003",
        "subject": "Weekly Newsletter: AI Engineering Digest #42",
        "sender": "newsletter@aidigest.example.com",
        "recipient": "me@example.com",
        "snippet": "This week in AI: local models, agents, and desktop architecture.",
        "body": "Here are the top articles this week...",
        "labels": ["INBOX", "Newsletters"],
        "date": datetime.now(timezone.utc).isoformat(),
    },
]


def ingest_email(
    remote_id: str,
    subject: str,
    sender: str,
    snippet: str,
    body: str,
    labels: list[str],
    date: str,
    recipient: str = "",
) -> int:
    labels_json = json.dumps(labels)
    with connect() as db:
        existing = db.execute("SELECT id FROM emails WHERE remote_id=?", (remote_id,)).fetchone()
        if existing:
            email_id = existing["id"]
            db.execute(
                "UPDATE emails SET subject=?, sender=?, recipient=?, snippet=?, body=?, labels=?, date=?, indexed_at=CURRENT_TIMESTAMP WHERE id=?",
                (subject, sender, recipient, snippet, body, labels_json, date, email_id),
            )
            db.execute("DELETE FROM emails_fts WHERE rowid=?", (email_id,))
            db.execute(
                "INSERT INTO emails_fts(rowid, subject, snippet, body) VALUES (?, ?, ?, ?)",
                (email_id, subject, snippet, body),
            )
            return email_id

        cursor = db.execute(
            "INSERT INTO emails(remote_id, subject, sender, recipient, snippet, body, labels, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (remote_id, subject, sender, recipient, snippet, body, labels_json, date),
        )
        email_id = cursor.lastrowid
        db.execute(
            "INSERT INTO emails_fts(rowid, subject, snippet, body) VALUES (?, ?, ?, ?)",
            (email_id, subject, snippet, body),
        )
        return email_id


def sync_gmail(
    filter_label: Optional[str] = None,
    after_timestamp: Optional[datetime] = None,
) -> dict[str, Any]:
    """Sync live Gmail with read-only OAuth; use labeled sample data otherwise."""
    try:
        access_token = get_google_access_token("gmail")
    except GoogleOAuthError:
        if not google_service_connected("gmail"):
            return _load_sample_gmail(filter_label)
        raise

    headers = {"Authorization": f"Bearer {access_token}"}
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me"
    params: dict[str, Any] = {"maxResults": 100}
    if after_timestamp:
        # Gmail's `after` filter uses whole Unix seconds. The small overlap lets
        # the caller recover messages when Gmail indexes them a little late.
        after_epoch = int((after_timestamp - timedelta(minutes=2)).timestamp())
        params["q"] = f"after:{after_epoch}"
    if filter_label:
        label_response = httpx.get(f"{base_url}/labels", headers=headers, timeout=20.0)
        if label_response.is_error:
            raise GoogleApiError(_gmail_api_error(label_response, "Gmail labels could not be read"))
        match = next((item["id"] for item in label_response.json().get("labels", []) if item.get("name") == filter_label), None)
        if match is None:
            return {"synced_count": 0, "filter_label": filter_label, "mode": "live"}
        params["labelIds"] = [match]

    messages: list[dict[str, str]] = []
    message_dates: list[tuple[str, str]] = []
    page_token = None
    with httpx.Client(timeout=30.0) as client:
        refreshed_after_unauthorized = False

        def gmail_get(url: str, request_params: dict[str, Any]) -> httpx.Response:
            nonlocal access_token, refreshed_after_unauthorized
            response = client.get(url, headers=headers, params=request_params)
            if response.status_code == 401 and not refreshed_after_unauthorized:
                access_token = get_google_access_token("gmail", force_refresh=True)
                headers["Authorization"] = f"Bearer {access_token}"
                refreshed_after_unauthorized = True
                response = client.get(url, headers=headers, params=request_params)
            return response

        while True:
            page_params = {**params}
            if page_token:
                page_params["pageToken"] = page_token
            response = gmail_get(f"{base_url}/messages", page_params)
            if response.is_error:
                raise GoogleApiError(_gmail_api_error(response, "Gmail messages could not be listed"))
            page = response.json()
            messages.extend(page.get("messages", []))
            page_token = page.get("nextPageToken")
            if not page_token:
                break

        for message in messages:
            response = gmail_get(
                f"{base_url}/messages/{message['id']}",
                {"format": "full"},
            )
            if response.is_error:
                raise GoogleApiError(_gmail_api_error(response, "A Gmail message could not be read"))
            item = response.json()
            payload = item.get("payload", {})
            message_headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}
            subject = message_headers.get("subject", "(no subject)")
            sender = message_headers.get("from", "")
            recipient = message_headers.get("to", "")
            body = _extract_message_body(payload)
            snippet = item.get("snippet", "")
            label_names = item.get("labelIds", [])
            message_date = datetime.fromtimestamp(int(item.get("internalDate", "0")) / 1000, timezone.utc).isoformat()
            message_dates.append((item["id"], message_date))
            ingest_email(
                remote_id=item["id"],
                subject=subject,
                sender=sender,
                recipient=recipient,
                snippet=snippet,
                body=body,
                labels=label_names,
                date=message_date,
            )
    result: dict[str, Any] = {"synced_count": len(messages), "filter_label": filter_label, "mode": "live"}
    if after_timestamp is not None:
        result["message_dates"] = message_dates
    return result


class GoogleApiError(RuntimeError):
    pass


def _gmail_api_error(response: httpx.Response, action: str) -> str:
    """Translate Google's API response into a useful, non-sensitive error."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        error = {}
    message = error.get("message")
    reasons = error.get("errors", [])
    reason = reasons[0].get("reason") if reasons and isinstance(reasons[0], dict) else ""
    status = response.status_code

    if status == 401:
        detail = "Google rejected the Gmail access token (401). Try again to refresh it; if this repeats, reconnect Gmail."
    elif status == 403 and reason == "accessNotConfigured":
        detail = "The Gmail API is not enabled for this Google Cloud project. Enable Gmail API in Google Cloud Console, then try again."
    elif status == 403 and reason in {"insufficientPermissions", "forbidden"}:
        detail = "Google denied the Gmail permission. Reconnect Gmail and approve read access to messages."
    elif status == 403 and reason in {"rateLimitExceeded", "userRateLimitExceeded"}:
        detail = "Google rate limited Gmail requests. Wait a few minutes and try again."
    elif status == 429:
        detail = "Google rate limited Gmail requests. Wait a few minutes and try again."
    elif status == 400:
        detail = "Google rejected the Gmail request (400)."
    elif status >= 500:
        detail = f"Google's Gmail service is temporarily unavailable ({status}). Try again shortly."
    else:
        detail = f"Google rejected the Gmail request ({status})."

    if isinstance(message, str) and message.strip():
        clean_message = " ".join(message.split())[:240]
        detail = f"{detail} Google says: {clean_message}"
    return f"{action}. {detail}"


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _decode_body(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_message_body(payload: dict[str, Any]) -> str:
    plain: list[str] = []
    html: list[str] = []

    def visit(part: dict[str, Any]) -> None:
        body = part.get("body", {}).get("data")
        mime_type = part.get("mimeType", "")
        if body:
            decoded = _decode_body(body)
            if mime_type == "text/plain":
                plain.append(decoded)
            elif mime_type == "text/html":
                html.append(decoded)
        for child in part.get("parts", []):
            visit(child)

    visit(payload)
    if plain:
        return "\n".join(plain)
    if html:
        parser = _HTMLText()
        for fragment in html:
            parser.feed(fragment)
        return " ".join(parser.parts)
    return ""


def _load_sample_gmail(filter_label: Optional[str]) -> dict[str, Any]:
    count = 0
    for sample in SAMPLE_GMAIL_MESSAGES:
        if filter_label and filter_label not in sample["labels"]:
            continue
        ingest_email(
            remote_id=sample["remote_id"],
            subject=sample["subject"],
            sender=sample["sender"],
            recipient=sample["recipient"],
            snippet=sample["snippet"],
            body=sample["body"],
            labels=sample["labels"],
            date=sample["date"],
        )
        count += 1
    return {"synced_count": count, "filter_label": filter_label, "mode": "sample"}


def list_emails(limit: int = 50, label: Optional[str] = None) -> list[dict[str, Any]]:
    with connect() as db:
        query = "SELECT id, remote_id, subject, sender, recipient, snippet, labels, date, indexed_at FROM emails"
        params: list[Any] = []
        if label:
            query += " WHERE labels LIKE ?"
            params.append(f"%{label}%")
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        rows = db.execute(query, tuple(params)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["labels"] = json.loads(d["labels"])
            except Exception:
                d["labels"] = []
            result.append(d)
        return result


def delete_email_from_leaves(email_id: int) -> bool:
    """Removes Leaves local copy and index only; leaves original email untouched."""
    with connect() as db:
        db.execute("DELETE FROM emails_fts WHERE rowid=?", (email_id,))
        cursor = db.execute("DELETE FROM emails WHERE id=?", (email_id,))
        return cursor.rowcount > 0


def get_task_relevant_emails(limit: int = 15, remote_ids: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """
    Filters only task-relevant emails to comply with the non-negotiable rule:
    'Send only task-relevant context to cloud LLMs, rather than sending the entire inbox.'
    """
    ACTION_KEYWORDS = ["urgent", "review", "deadline", "by tomorrow", "please", "action", "follow up", "due", "important"]
    with connect() as db:
        query = "SELECT id, remote_id, subject, sender, snippet, body, date FROM emails"
        params: tuple[Any, ...] = ()
        if remote_ids is not None:
            if not remote_ids:
                return []
            placeholders = ",".join("?" for _ in remote_ids)
            query += f" WHERE remote_id IN ({placeholders})"
            params = tuple(remote_ids)
        query += " ORDER BY date DESC"
        rows = db.execute(query, params).fetchall()
        candidates = []
        for r in rows:
            text = f"{r['subject']} {r['snippet']} {r['body']}".lower()
            if any(k in text for k in ACTION_KEYWORDS):
                candidates.append({
                    "source_type": "email",
                    "source_ref": f"email:{r['remote_id']}",
                    "title": r["subject"],
                    "content": f"From: {r['sender']}\nSubject: {r['subject']}\nDate: {r['date']}\n\n{r['body'][:500]}",
                })
                if len(candidates) >= limit:
                    break
        return candidates
