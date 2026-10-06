"""
Document ingestion pipeline re-export.
"""

from app.rag.ingest import (
    load_source_register,
    ingest_document_file,
    ingest_all_documents,
)

__all__ = [
    "load_source_register",
    "ingest_document_file",
    "ingest_all_documents",
]
