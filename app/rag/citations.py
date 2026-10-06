"""
Citation formatting and validation re-export.
Re-exports from app.services.citation.
"""

from app.services.citation import (
    format_citation,
    format_citation_string,
    deduplicate_citations,
    CitationService,
)

__all__ = [
    "format_citation",
    "format_citation_string",
    "deduplicate_citations",
    "CitationService",
]
