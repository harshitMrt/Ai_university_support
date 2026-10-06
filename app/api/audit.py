"""
Audit log endpoints.
GET /audit/{trace_id}
GET /audit
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from app.audit.logger import get_audit_record, list_audit_records

router = APIRouter(tags=["Audit & Observability"])


@router.get("/audit/{trace_id}")
async def get_audit_by_trace(trace_id: str):
    record = get_audit_record(trace_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Audit trace record '{trace_id}' not found."
        )
    return record


@router.get("/audit")
async def get_recent_audits(limit: int = Query(25, ge=1, le=100)):
    records = list_audit_records(limit=limit)
    return {"count": len(records), "records": records}
