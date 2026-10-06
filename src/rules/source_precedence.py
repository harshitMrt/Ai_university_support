"""
Authoritative source precedence service re-export.
"""

from app.services.source_resolution import resolve_authoritative_sources, parse_date

__all__ = ["resolve_authoritative_sources", "parse_date"]
