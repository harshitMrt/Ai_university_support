"""
Security input validation for queries and file uploads.
Re-exports from app.core.security for backward compatibility.
"""

from app.core.security import validate_question_text, validate_file_upload

__all__ = ["validate_question_text", "validate_file_upload"]
