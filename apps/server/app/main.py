from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.database import connect, initialize_database
from app.services.indexing import add_source, refresh_source, remove_source
from app.services.search import search_documents


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Leaves Local API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class SourceInput(BaseModel):
    path: str
    recursive: bool = True


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "leaves-local"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    with connect() as db:
        source_count = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        document_count = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        sources = [dict(row) for row in db.execute(
            "SELECT id, path, recursive, created_at, last_indexed_at FROM sources ORDER BY created_at DESC"
        ).fetchall()]
        recent = [dict(row) for row in db.execute(
            "SELECT title, path, modified_at FROM documents ORDER BY modified_at DESC LIMIT 5"
        ).fetchall()]
    return {"source_count": source_count, "document_count": document_count, "sources": sources, "recent_documents": recent}


@app.get("/api/sources")
def list_sources() -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT id, path, recursive, created_at, last_indexed_at FROM sources ORDER BY created_at DESC"
        ).fetchall()]


@app.post("/api/sources")
def create_source(payload: SourceInput) -> dict:
    try:
        return add_source(payload.path, payload.recursive)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=400, detail="Could not read the selected folder.") from error


@app.post("/api/sources/{source_id}/refresh")
def refresh(source_id: int) -> dict:
    try:
        return refresh_source(source_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: int) -> dict:
    if not remove_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"deleted": True, "original_files_deleted": False}


@app.get("/api/search")
def search(q: str = Query(default="", max_length=300), limit: int = Query(default=30, ge=1, le=100)) -> list[dict]:
    try:
        return search_documents(q, limit)
    except Exception as error:
        raise HTTPException(status_code=400, detail="Search could not be completed.") from error
