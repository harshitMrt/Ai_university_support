"""
GET /sources endpoint.
Returns the master catalog of authoritative university documents and metadata.
"""

from fastapi import APIRouter
from app.rag.ingest import load_source_register
from app.schemas.responses import SourceCatalogResponse

router = APIRouter(tags=["Source Register"])


@router.get("/sources", response_model=SourceCatalogResponse)
async def list_sources():
    sources = load_source_register()
    return SourceCatalogResponse(
        count=len(sources),
        sources=sources
    )
