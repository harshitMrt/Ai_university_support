"""
ChromaDB Retriever and Vector Store interface.
Persists vectors to disk and supports semantic similarity search with metadata filtering.
"""

from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.embeddings import embed_query

COLLECTION_NAME = "university_regulations"
_CHROMA_CLIENT = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _CHROMA_CLIENT


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def query_documents(
    query: str,
    top_k: int = 5,
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_vector = embed_query(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if results and results.get("documents") and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        ids = results["ids"][0] if results.get("ids") else [f"chunk_{i}" for i in range(len(docs))]

        for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
            chunks.append({
                "id": chunk_id,
                "text": text,
                "metadata": meta,
                "distance": dist,
                # Cosine similarity roughly 1 - distance
                "score": max(0.0, 1.0 - dist)
            })

    return chunks


def get_collection_count() -> int:
    try:
        col = get_collection()
        return col.count()
    except Exception:
        return 0
