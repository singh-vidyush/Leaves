from typing import Any

from app.core.database import connect


def list_notifications(unread_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    with connect() as db:
        query = "SELECT * FROM notifications"
        if unread_only:
            query += " WHERE is_read=0"
        query += " ORDER BY created_at DESC LIMIT ?"
        rows = db.execute(query, (limit,)).fetchall()
        return [dict(r) for r in rows]


def mark_notification_read(notification_id: int) -> bool:
    with connect() as db:
        cursor = db.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
        return cursor.rowcount > 0


def mark_all_notifications_read() -> int:
    with connect() as db:
        cursor = db.execute("UPDATE notifications SET is_read=1 WHERE is_read=0")
        return cursor.rowcount
