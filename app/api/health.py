"""
GET /health endpoint.
Reports operational health across API, SQLite database, ChromaDB vector store, and Ollama.
Degrades gracefully without crashing if any dependency has issues.
"""

import httpx
from fastapi import APIRouter
from app.core.config import settings
from app.database.connection import get_connection
from app.rag.retriever import get_collection_count
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["System Health"])


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
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students;")
            count = cursor.fetchone()[0]
            db_ok = count > 0
        finally:
            conn.close()
    except Exception:
        db_ok = False

    # 2. ChromaDB check
    try:
        from app.rag.retriever import get_collection
        col = get_collection()
        indexed_chunks = col.count()
        chroma_ok = True
    except Exception:
        chroma_ok = False

    # 3. Ollama check with fast connect timeout
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        timeout_cfg = httpx.Timeout(2.0, connect=settings.LLM_CONNECT_TIMEOUT_SEC)
        with httpx.Client(timeout=timeout_cfg) as client:
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
