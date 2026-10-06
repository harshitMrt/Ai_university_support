"""
Citation formatting and validation service.
Constructs transparent, traceable citations from authoritative document metadata.
"""

from typing import Any, Dict, List


class CitationService:
    @staticmethod
    def format_citation(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs standardized citation dictionary matching regulatory requirements.
        """
        return {
            "title": metadata.get("title", "Official University Document"),
            "section": metadata.get("section", "General Section"),
            "page": metadata.get("page", 1),
            "version": str(metadata.get("version", "1.0")),
            "effective_date": str(metadata.get("effective_from", "N/A")),
            "doc_id": metadata.get("doc_id", "UNKNOWN"),
            "authority_level": int(metadata.get("authority_level", 1)),
        }

    @staticmethod
    def format_citation_string(citation: Dict[str, Any]) -> str:
        """
        Formats citation into a clean markdown block.
        """
        lines = [
            f"**Source:** {citation.get('title')}",
            f"- **Section:** {citation.get('section')}",
            f"- **Page:** {citation.get('page')}",
            f"- **Version:** {citation.get('version')}",
            f"- **Effective Date:** {citation.get('effective_date')}",
            f"- **Document ID:** {citation.get('doc_id')}",
        ]
        return "\n".join(lines)

    @staticmethod
    def deduplicate_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for c in citations:
            key = (c.get("doc_id"), c.get("section"), str(c.get("version")))
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        return deduped


format_citation = CitationService.format_citation
format_citation_string = CitationService.format_citation_string
deduplicate_citations = CitationService.deduplicate_citations
