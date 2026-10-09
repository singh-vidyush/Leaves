from datetime import datetime, timezone
import hashlib
from pathlib import Path

from app.core.database import connect


MARKDOWN_EXTENSIONS = {".md", ".markdown"}


def add_source(folder: str, recursive: bool = True) -> dict:
    path = Path(folder).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise ValueError("Choose a folder to add as a source.")
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO sources(path, recursive) VALUES (?, ?) "
            "ON CONFLICT(path) DO UPDATE SET recursive=excluded.recursive RETURNING id, path, recursive",
            (str(path), int(recursive)),
        )
        source = dict(cursor.fetchone())
    return refresh_source(source["id"])


def refresh_source(source_id: int) -> dict:
    with connect() as db:
        source_row = db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if source_row is None:
            raise LookupError("Source not found.")
        source = dict(source_row)

    root = Path(source["path"])
    if not root.is_dir():
        raise FileNotFoundError("The selected folder is no longer available.")

    candidates = root.rglob("*") if source["recursive"] else root.glob("*")
    seen: set[str] = set()
    indexed = 0
    for file_path in candidates:
        if not file_path.is_file() or file_path.suffix.lower() not in MARKDOWN_EXTENSIONS:
            continue
        resolved = file_path.resolve()
        if not resolved.is_relative_to(root):
            continue
        try:
            content = file_path.read_text(encoding="utf-8-sig", errors="replace")
            modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat()
        except OSError:
            continue

        document_path = str(resolved)
        seen.add(document_path)
        title = next(
            (line.lstrip("# ").strip() for line in content.splitlines() if line.strip()),
            file_path.stem,
        )
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        with connect() as db:
            previous = db.execute(
                "SELECT id, content_hash FROM documents WHERE path=?", (document_path,)
            ).fetchone()
            if previous and previous["content_hash"] == content_hash:
                db.execute(
                    "UPDATE documents SET modified_at=?, indexed_at=CURRENT_TIMESTAMP WHERE id=?",
                    (modified_at, previous["id"]),
                )
                continue
            if previous:
                document_id = previous["id"]
                db.execute("DELETE FROM documents_fts WHERE rowid=?", (document_id,))
                db.execute(
                    "UPDATE documents SET source_id=?, title=?, content=?, content_hash=?, modified_at=?, indexed_at=CURRENT_TIMESTAMP WHERE id=?",
                    (source_id, title, content, content_hash, modified_at, document_id),
                )
            else:
                cursor = db.execute(
                    "INSERT INTO documents(source_id, path, title, content, content_hash, modified_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (source_id, document_path, title, content, content_hash, modified_at),
                )
                document_id = cursor.lastrowid
            db.execute(
                "INSERT INTO documents_fts(rowid, title, content, path) VALUES (?, ?, ?, ?)",
                (document_id, title, content, document_path),
            )
        indexed += 1

    with connect() as db:
        existing = db.execute("SELECT id, path FROM documents WHERE source_id=?", (source_id,)).fetchall()
        for row in existing:
            if row["path"] not in seen:
                db.execute("DELETE FROM documents_fts WHERE rowid=?", (row["id"],))
                db.execute("DELETE FROM documents WHERE id=?", (row["id"],))
        db.execute("UPDATE sources SET last_indexed_at=CURRENT_TIMESTAMP WHERE id=?", (source_id,))

    return {"id": source_id, "path": source["path"], "recursive": bool(source["recursive"]), "indexed": indexed}


def remove_source(source_id: int) -> bool:
    with connect() as db:
        documents = db.execute("SELECT id FROM documents WHERE source_id=?", (source_id,)).fetchall()
        for row in documents:
            db.execute("DELETE FROM documents_fts WHERE rowid=?", (row["id"],))
        cursor = db.execute("DELETE FROM sources WHERE id=?", (source_id,))
        return cursor.rowcount > 0
