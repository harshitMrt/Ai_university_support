"""
POST /ingest endpoint for live document ingestion.
Supports immediate ingestion into ChromaDB without server restart.
Handles multipart file uploads (PDF, TXT, DOCX, MD) with rich metadata.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import pandas as pd
from app.core.config import settings
from app.core.security import validate_file_upload
from app.rag.ingest import ingest_document_file
from app.schemas.responses import IngestJsonResponse

router = APIRouter(tags=["Document Ingestion"])


@router.post("/ingest", response_model=IngestJsonResponse)
async def ingest_document(
    file: UploadFile = File(..., description="Upload policy document (.pdf, .txt, .docx, .md)"),
    doc_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    authority_level: Optional[int] = Form(2),
    doc_type: Optional[str] = Form("Circular"),
    version: Optional[str] = Form("1.0"),
    effective_from: Optional[str] = Form("2026-10-06"),
    effective_to: Optional[str] = Form(""),
    supersedes: Optional[str] = Form(""),
    scope_programmes: Optional[str] = Form("ALL"),
    scope_batches: Optional[str] = Form("ALL"),
    issuer: Optional[str] = Form("Registrar Office")
):
    content = await file.read()
    is_valid, err_msg = validate_file_upload(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    safe_doc_id = (doc_id or Path(file.filename).stem).strip()
    target_path = settings.DOCUMENTS_DIR / f"{safe_doc_id}{Path(file.filename).suffix.lower()}"

    with open(target_path, "wb") as f:
        f.write(content)

    meta_override = {
        "doc_id": safe_doc_id,
        "title": title or safe_doc_id.replace("-", " ").title(),
        "authority_level": authority_level,
        "doc_type": doc_type,
        "version": version,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "supersedes": supersedes,
        "scope_programmes": scope_programmes,
        "scope_batches": scope_batches,
        "issuer": issuer,
        "provenance": f"Live Ingest API: {file.filename}"
    }

    try:
        ingest_res = ingest_document_file(target_path, metadata_override=meta_override)

        # Update source_register.csv so newly uploaded documents appear in catalog
        try:
            reg_path = Path(settings.SOURCE_REGISTER_PATH)
            if reg_path.exists() and reg_path.stat().st_size > 0:
                df = pd.read_csv(reg_path)
            else:
                df = pd.DataFrame()

            if not df.empty and "doc_id" in df.columns:
                df = df[df["doc_id"] != safe_doc_id]

            new_row = pd.DataFrame([ingest_res["metadata"]])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(reg_path, index=False)
        except Exception:
            pass

        return IngestJsonResponse(**ingest_res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
