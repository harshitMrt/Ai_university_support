"""
ChromaDB Persistent Vector Store Manager.
Manages database initialization, collection handles, and vector indices.
"""

from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

COLLECTION_NAME = "university_regulations"
_CHROMA_CLIENT: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _CHROMA_CLIENT


def get_collection():
    """
    Returns the persistent ChromaDB collection configured with cosine similarity.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def get_collection_count() -> int:
    try:
        col = get_collection()
        return col.count()
    except Exception:
        return 0
