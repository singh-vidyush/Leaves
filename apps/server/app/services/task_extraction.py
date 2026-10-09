import logging
from typing import Any, Optional

from app.adapters.manager import extract_tasks_from_context
from app.core.database import connect
from app.integrations.gmail.service import get_task_relevant_emails

logger = logging.getLogger("leaves.task_extraction")


def gather_permitted_task_context(max_docs: int = 10) -> list[dict[str, Any]]:
    """
    Collects ONLY task-relevant excerpts across authorized local sources:
    - User-selected Markdown documents
    - Emails identified as relevant to a task (not the entire inbox)
    Calendar event text is deliberately excluded; event times stay local for scheduling.
    """
    context: list[dict[str, Any]] = []

    # 1. Markdown documents
    with connect() as db:
        rows = db.execute("SELECT id, path, title, content FROM documents ORDER BY modified_at DESC LIMIT ?", (max_docs,)).fetchall()
        for r in rows:
            # Send first 1000 characters or lines matching task patterns
            context.append({
                "source_type": "markdown",
                "source_ref": r["path"],
                "title": r["title"],
                "content": r["content"][:1000],
            })

    # 2. Task-relevant emails only
    emails = get_task_relevant_emails(limit=10)
    context.extend(emails)

    return context


def extract_and_store_tasks() -> list[dict[str, Any]]:
    context = gather_permitted_task_context()
    return extract_and_store_tasks_from_context(context)


def extract_and_store_tasks_from_context(context: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract and upsert tasks from an explicitly selected source context."""
    if not context:
        return []

    proposals = extract_tasks_from_context(context)
    stored_tasks = []

    with connect() as db:
        for p in proposals:
            title = p.get("title", "").strip()
            if not title:
                continue

            source_type = p.get("source_type", "unknown")
            source_ref = p.get("source_ref", "")
            description = p.get("description", "")
            urgency_score = int(p.get("urgency_score", 5))
            urgency_reason = p.get("urgency_reason", "Standard priority")
            duration = int(p.get("suggested_duration_minutes", 30))
            deadline = p.get("deadline")

            # Check if task already exists
            existing = db.execute(
                "SELECT id, status FROM tasks WHERE title=? AND source_ref=?",
                (title, source_ref),
            ).fetchone()

            if existing:
                # Update urgency and details if still pending
                if existing["status"] == "pending":
                    db.execute(
                        "UPDATE tasks SET urgency_score=?, urgency_reason=?, suggested_duration_minutes=?, deadline=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (urgency_score, urgency_reason, duration, deadline, existing["id"]),
                    )
                task_id = existing["id"]
            else:
                cursor = db.execute(
                    "INSERT INTO tasks(title, description, source_type, source_ref, urgency_score, urgency_reason, suggested_duration_minutes, deadline, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                    (title, description, source_type, source_ref, urgency_score, urgency_reason, duration, deadline),
                )
                task_id = cursor.lastrowid

            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            stored_tasks.append(dict(row))

    return stored_tasks


def list_tasks(status: Optional[str] = None) -> list[dict[str, Any]]:
    with connect() as db:
        query = "SELECT * FROM tasks"
        params: list[Any] = []
        if status:
            query += " WHERE status=?"
            params.append(status)
        query += " ORDER BY urgency_score DESC, deadline ASC, created_at DESC"
        rows = db.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]


def update_task_status(task_id: int, status: str) -> dict[str, Any]:
    with connect() as db:
        db.execute("UPDATE tasks SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, task_id))
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise LookupError(f"Task {task_id} not found.")
        return dict(row)
