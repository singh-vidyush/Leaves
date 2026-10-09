from datetime import datetime, timezone
import json
from typing import Any

from app.core.database import connect


def export_leaves_data() -> dict[str, Any]:
    """
    Exports all Leaves-held local data in portable JSON format.
    Never exports private API keys or OAuth secrets.
    """
    with connect() as db:
        sources = [dict(r) for r in db.execute("SELECT * FROM sources").fetchall()]
        documents = [dict(r) for r in db.execute("SELECT id, source_id, path, title, content, modified_at, indexed_at FROM documents").fetchall()]
        emails = []
        for r in db.execute("SELECT * FROM emails").fetchall():
            d = dict(r)
            try:
                d["labels"] = json.loads(d["labels"])
            except Exception:
                pass
            emails.append(d)
        calendar_events = [dict(r) for r in db.execute("SELECT * FROM calendar_events").fetchall()]
        tasks = [dict(r) for r in db.execute("SELECT * FROM tasks").fetchall()]
        notifications = [dict(r) for r in db.execute("SELECT * FROM notifications").fetchall()]
        settings = [dict(r) for r in db.execute("SELECT key, value, updated_at FROM settings").fetchall()]

    return {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "documents": documents,
        "emails": emails,
        "calendar_events": calendar_events,
        "tasks": tasks,
        "notifications": notifications,
        "settings": settings,
    }
