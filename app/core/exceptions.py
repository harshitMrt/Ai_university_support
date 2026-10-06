"""
Domain-specific exceptions with corresponding HTTP status codes.
Prevents internal leaking while enabling clear API error boundaries.
"""

from typing import Optional


class UniversityAppException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = 500, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class StudentNotFoundError(UniversityAppException):
    def __init__(self, student_id: str):
        super().__init__(
            message=f"Student record '{student_id}' not found.",
            status_code=404,
            detail=f"No record matching identifier '{student_id}' was located in the student database."
        )


class UnauthorizedPrivacyViolationError(UniversityAppException):
    def __init__(self, detail: str):
        super().__init__(
            message="Unauthorized access to student personal records is strictly prohibited.",
            status_code=403,
            detail=detail
        )


class PromptInjectionDetectedError(UniversityAppException):
    def __init__(self, detail: str):
        super().__init__(
            message="Prompt injection or security override pattern detected.",
            status_code=400,
            detail=detail
        )


class InvalidInputValidationError(UniversityAppException):
    def __init__(self, detail: str):
        super().__init__(
            message="Input validation failed.",
            status_code=422,
            detail=detail
        )


class DocumentIngestionError(UniversityAppException):
    def __init__(self, detail: str):
        super().__init__(
            message="Document ingestion failed.",
            status_code=500,
            detail=detail
        )
