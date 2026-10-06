"""
Prompt Injection Defense and Document Safety Layer.
Re-exports from app.core.security for backward compatibility.
"""

from app.core.security import (
    INJECTION_PATTERNS,
    DOCUMENT_DEFENSE_PROMPT,
    inspect_prompt_injection,
    sanitize_document_text,
)

__all__ = [
    "INJECTION_PATTERNS",
    "DOCUMENT_DEFENSE_PROMPT",
    "inspect_prompt_injection",
    "sanitize_document_text",
]
