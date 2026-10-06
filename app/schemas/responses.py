"""
Response schemas matching existing API contracts.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskResponse(BaseModel):
    trace_id: str
    answer_type: str
    answer: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tools_invoked: List[str] = Field(default_factory=list)
    applied_rules: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts_detected: List[str] = Field(default_factory=list)
    policy_notes: List[str] = Field(default_factory=list)
    audit_id: str
    latency_ms: float = 0.0


class HealthResponse(BaseModel):
    status: str
    api: bool
    database: bool
    chromadb: bool
    ollama: bool
    model: str
    indexed_chunks: int = 0


class IngestJsonResponse(BaseModel):
    doc_id: str
    title: str
    version: str
    authority_level: int
    chunks_created: int
    embedding_status: str
    metadata: Dict[str, Any]
    ingestion_timestamp: str
    file_name: str


class SourceCatalogResponse(BaseModel):
    count: int
    sources: List[Dict[str, Any]]


class AuditListResponse(BaseModel):
    count: int
    records: List[Dict[str, Any]]
