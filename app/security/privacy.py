"""
Privacy and Authorization Controls for Student Personal Data.
Re-exports from app.core.security for backward compatibility.
"""

from app.core.security import (
    STUDENT_ID_PATTERN,
    EXPLICIT_STUDENT_ID_PATTERN,
    PROMPT_INJECTION_PATTERN,
    OTHER_STUDENT_PATTERNS,
    inspect_privacy_boundaries,
)

__all__ = [
    "STUDENT_ID_PATTERN",
    "EXPLICIT_STUDENT_ID_PATTERN",
    "PROMPT_INJECTION_PATTERN",
    "OTHER_STUDENT_PATTERNS",
    "inspect_privacy_boundaries",
]
