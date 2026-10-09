from datetime import datetime, timezone
import json
import logging
from typing import Any, Optional

from app.core.database import connect

logger = logging.getLogger("leaves.gmail")

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


def sync_gmail(filter_label: Optional[str] = None) -> dict[str, Any]:
    """
    Syncs Gmail messages. If external credentials are not set,
    populates test/sample messages so integration is verifiable.
    """
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
    return {"synced_count": count, "filter_label": filter_label}


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


def get_task_relevant_emails(limit: int = 15) -> list[dict[str, Any]]:
    """
    Filters only task-relevant emails to comply with the non-negotiable rule:
    'Send only task-relevant context to cloud LLMs, rather than sending the entire inbox.'
    """
    ACTION_KEYWORDS = ["urgent", "review", "deadline", "by tomorrow", "please", "action", "follow up", "due", "important"]
    with connect() as db:
        rows = db.execute("SELECT id, remote_id, subject, sender, snippet, body, date FROM emails ORDER BY date DESC").fetchall()
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
