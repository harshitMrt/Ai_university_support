"""
GET /health endpoint.
Reports operational health across API, SQLite database, ChromaDB vector store, and Ollama.
Degrades gracefully without crashing if any dependency has issues.
"""

from typing import Any, Dict
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings
from app.db.database import get_connection
from app.rag.retriever import get_collection_count

router = APIRouter(tags=["System Health"])


class HealthResponse(BaseModel):
    status: str
    api: bool
    database: bool
    chromadb: bool
    ollama: bool
    model: str
    indexed_chunks: int = 0


@router.get("/health", response_model=HealthResponse)
async def check_system_health():
    api_ok = True
    db_ok = False
    chroma_ok = False
    ollama_ok = False
    indexed_chunks = 0

    # 1. Database check
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students;")
        count = cursor.fetchone()[0]
        conn.close()
        db_ok = count > 0
    except Exception:
        db_ok = False

    # 2. ChromaDB check
    try:
        indexed_chunks = get_collection_count()
        chroma_ok = indexed_chunks > 0
    except Exception:
        chroma_ok = False

    # 3. Ollama check
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(url)
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    all_ok = api_ok and db_ok and chroma_ok and ollama_ok
    status = "ok" if all_ok else "degraded"

    return HealthResponse(
        status=status,
        api=api_ok,
        database=db_ok,
        chromadb=chroma_ok,
        ollama=ollama_ok,
        model=settings.OLLAMA_MODEL,
        indexed_chunks=indexed_chunks
    )
