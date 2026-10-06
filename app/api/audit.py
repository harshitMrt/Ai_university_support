"""
Audit log endpoints.
GET /audit/{trace_id}
GET /audit
"""

from fastapi import APIRouter, HTTPException, Query
from app.repositories.audit_repository import AuditRepository
from app.schemas.responses import AuditListResponse

router = APIRouter(tags=["Audit & Observability"])


@router.get("/audit/{trace_id}")
async def get_audit_by_trace(trace_id: str):
    record = AuditRepository.get_by_trace_id(trace_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Audit trace record '{trace_id}' not found."
        )
    return record


@router.get("/audit", response_model=AuditListResponse)
async def get_recent_audits(limit: int = Query(25, ge=1, le=100)):
    records = AuditRepository.list_recent(limit=limit)
    return AuditListResponse(count=len(records), records=records)
