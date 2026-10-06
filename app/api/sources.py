"""
GET /sources endpoint.
Returns the master catalog of authoritative university documents and metadata.
"""

from typing import Any, Dict, List
from fastapi import APIRouter
from app.rag.ingest import load_source_register

router = APIRouter(tags=["Source Register"])


@router.get("/sources")
async def list_sources():
    sources = load_source_register()
    return {
        "count": len(sources),
        "sources": sources
    }
