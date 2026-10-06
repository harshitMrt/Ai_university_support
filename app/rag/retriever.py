"""
ChromaDB Retriever interface.
Supports semantic similarity search with metadata filtering and normalized cosine scores.
"""

from typing import Any, Dict, List, Optional
from app.rag.embeddings import embed_query
from app.rag.vector_store import get_chroma_client, get_collection, get_collection_count, COLLECTION_NAME


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


__all__ = [
    "COLLECTION_NAME",
    "get_chroma_client",
    "get_collection",
    "query_documents",
    "get_collection_count",
]
