"""
FastAPI route dependencies.
Handles authentication context extraction and validation.
"""

from typing import Optional
from fastapi import Header, HTTPException


async def get_authenticated_student_id(
    x_student_id: Optional[str] = Header(None, alias="X-Student-Id")
) -> str:
    """
    Extracts and validates mandatory X-Student-Id header from incoming HTTP request.
    Raises 400 Bad Request if missing or whitespace.
    """
    if not x_student_id or not x_student_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Missing required header 'X-Student-Id'. Please provide a valid student identifier."
        )
    return x_student_id.strip()
