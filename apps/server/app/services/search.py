import re

from app.core.database import connect


def search_documents(query: str, limit: int = 30) -> list[dict]:
    terms = re.findall(r"[\w'-]+", query, flags=re.UNICODE)
    if not terms:
        return []
    match_query = " AND ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
    with connect() as db:
        rows = db.execute(
            """
            SELECT d.id, d.path, d.title, d.modified_at,
                   snippet(documents_fts, 1, ?, ?, ' … ', 22) AS excerpt
            FROM documents_fts
            JOIN documents d ON d.id=documents_fts.rowid
            WHERE documents_fts MATCH ?
            ORDER BY bm25(documents_fts), d.modified_at DESC
            LIMIT ?
            """,
            ("\u0001", "\u0002", match_query, max(1, min(limit, 100))),
        ).fetchall()
    return [dict(row) for row in rows]
