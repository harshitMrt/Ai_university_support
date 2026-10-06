"""
Request schemas with robust validation rules.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Student's query about policies, attendance, marks, or eligibility"
    )
    as_of_date: Optional[str] = Field(
        "2026-10-06",
        description="Effective date for evaluation (YYYY-MM-DD)"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or pure whitespace.")
        return cleaned

    @field_validator("as_of_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return "2026-10-06"
        cleaned = v.strip()
        if not DATE_REGEX.match(cleaned):
            raise ValueError("as_of_date must be formatted as YYYY-MM-DD.")
        return cleaned
