"""
Document ingestion pipeline for ChromaDB.
Supports:
1. Batch initial ingestion from data/source_register.csv and data/documents/
2. Dynamic live single document ingestion (POST /ingest) without restarting the server.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from app.config import settings
from app.rag.chunking import extract_text_from_file, chunk_document
from app.rag.embeddings import embed_texts
from app.rag.retriever import get_collection


def load_source_register(csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(csv_path or settings.SOURCE_REGISTER_PATH)
    if not path.exists():
        return []
    df = pd.read_csv(path)
    df = df.fillna("")
    return df.to_dict(orient="records")


def ingest_document_file(
    file_path: Path,
    metadata_override: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ingests a single document into ChromaDB immediately.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = extract_text_from_file(file_path)
    if not text.strip():
        raise ValueError(f"Extracted document text is empty: {file_path.name}")

    meta = metadata_override or {}
    doc_id = meta.get("doc_id") or file_path.stem

    base_metadata = {
        "doc_id": doc_id,
        "title": meta.get("title", file_path.stem.replace("-", " ").title()),
        "issuer": meta.get("issuer", "University Administration"),
        "authority_level": int(meta.get("authority_level", 2)),
        "doc_type": meta.get("doc_type", "Policy"),
        "version": str(meta.get("version", "1.0")),
        "effective_from": str(meta.get("effective_from", datetime.now().strftime("%Y-%m-%d"))),
        "effective_to": str(meta.get("effective_to", "")),
        "supersedes": str(meta.get("supersedes", "")),
        "scope_programmes": str(meta.get("scope_programmes", "ALL")),
        "scope_batches": str(meta.get("scope_batches", "ALL")),
        "provenance": str(meta.get("provenance", f"Uploaded File: {file_path.name}")),
        "retrieved_on": datetime.now().strftime("%Y-%m-%d"),
        "synthetic": "TRUE",
    }

    chunks = chunk_document(text, base_metadata)
    if not chunks:
        raise ValueError("No chunks generated from document text.")

    chunk_texts = [c["text"] for c in chunks]
    chunk_ids = [c["id"] for c in chunks]
    chunk_metadatas = [c["metadata"] for c in chunks]

    # Generate embeddings
    embeddings = embed_texts(chunk_texts)

    collection = get_collection()

    # Delete previous chunks with same doc_id to support live re-ingestion/updates
    try:
        existing = collection.get(where={"doc_id": doc_id})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    collection.add(
        ids=chunk_ids,
        documents=chunk_texts,
        metadatas=chunk_metadatas,
        embeddings=embeddings
    )

    return {
        "doc_id": doc_id,
        "title": base_metadata["title"],
        "version": base_metadata["version"],
        "authority_level": base_metadata["authority_level"],
        "chunks_created": len(chunks),
        "embedding_status": "SUCCESS",
        "metadata": base_metadata,
        "ingestion_timestamp": datetime.now().isoformat(),
        "file_name": file_path.name
    }


def ingest_all_documents() -> List[Dict[str, Any]]:
    """
    Ingests all cataloged documents from the source register into ChromaDB.
    """
    records = load_source_register()
    results = []

    for rec in records:
        doc_id = rec.get("doc_id")
        # Check files in documents directory
        matching_files = list(settings.DOCUMENTS_DIR.glob(f"{doc_id}.*"))
        if not matching_files:
            continue

        file_path = matching_files[0]
        try:
            res = ingest_document_file(file_path, rec)
            results.append(res)
        except Exception as e:
            print(f"Error ingesting {doc_id}: {e}")

    return results


if __name__ == "__main__":
    print("Ingesting all university documents into ChromaDB...")
    ingested = ingest_all_documents()
    print(f"Successfully ingested {len(ingested)} documents into ChromaDB.")
