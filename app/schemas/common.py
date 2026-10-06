"""
Common schemas, enums, and data contracts across the university student services system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnswerType(str, Enum):
    RETRIEVED_FACT = "retrieved_fact"
    CALCULATED = "calculated"
    NOT_FOUND = "not_found"
    CLARIFICATION_NEEDED = "clarification_needed"
    REFUSED = "refused"
    CONFLICT_FLAGGED = "conflict_flagged"


class ExamType(str, Enum):
    REGULAR = "REGULAR"
    END_SEM = "END_SEM"
    SUPPLEMENTARY = "SUPPLEMENTARY"


class CitationItem(BaseModel):
    title: str = Field(..., description="Document official title")
    section: str = Field(..., description="Document section reference")
    page: int = Field(1, description="Page number")
    version: str = Field("1.0", description="Document version string")
    effective_date: str = Field("N/A", description="Effective date ISO string")
    doc_id: str = Field(..., description="Document unique identifier")
    authority_level: int = Field(1, description="Authority hierarchy level (1-5)")
