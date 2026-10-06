"""
Input validation and file integrity checks.
"""

from pathlib import Path
from typing import List, Tuple
from app.config import settings


def validate_file_upload(filename: str, file_size_bytes: int) -> Tuple[bool, str]:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format '{suffix}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_MB}MB."

    return True, ""


def validate_question_text(question: str) -> Tuple[bool, str]:
    if not question or not question.strip():
        return False, "Question cannot be empty."
    if len(question.strip()) < 3:
        return False, "Question is too short to process."
    if len(question) > 2000:
        return False, "Question exceeds maximum character length (2000)."
    return True, ""
