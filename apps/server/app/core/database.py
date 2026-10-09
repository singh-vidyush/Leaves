from contextlib import contextmanager
import sqlite3
from typing import Iterator

from .config import database_path


def initialize_database() -> None:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                recursive INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_indexed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                title, content, path, content='documents', content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                remote_id TEXT NOT NULL UNIQUE,
                subject TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL DEFAULT '',
                snippet TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                labels TEXT NOT NULL DEFAULT '[]',
                date TEXT NOT NULL,
                indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
                subject, snippet, body, content='emails', content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY,
                remote_id TEXT UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_by TEXT NOT NULL DEFAULT 'external',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                urgency_score INTEGER NOT NULL DEFAULT 5,
                urgency_reason TEXT NOT NULL DEFAULT '',
                suggested_duration_minutes INTEGER NOT NULL DEFAULT 30,
                deadline TEXT,
                scheduled_event_id INTEGER REFERENCES calendar_events(id) ON DELETE SET NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                event_id INTEGER REFERENCES calendar_events(id) ON DELETE SET NULL,
                task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    initialize_database()
    connection = sqlite3.connect(database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
