"""
Local Embedding model pipeline using Sentence-Transformers.
Defaults to lightweight 'all-MiniLM-L6-v2' (or configurable via settings).
Runs entirely locally without cloud API dependencies.
"""

from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings

_EMBEDDER_INSTANCE = None


def get_embedder() -> SentenceTransformer:
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        _EMBEDDER_INSTANCE = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _EMBEDDER_INSTANCE


def embed_texts(texts: List[str]) -> List[List[float]]:
    embedder = get_embedder()
    embeddings = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    embedder = get_embedder()
    emb = embedder.encode(query, show_progress_bar=False, normalize_embeddings=True)
    return emb.tolist()
