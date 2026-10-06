"""
Repository for accessing regulatory rules stored in SQLite rule_registry table.
"""

from typing import Any, Dict, List, Optional
from app.database.connection import get_connection


class RuleRepository:
    @staticmethod
    def get_all_rules() -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rule_id, description, parameter, operator, threshold_value,
                       scope_programmes, scope_batches, effective_from, effective_to,
                       source_doc_id, source_section
                FROM rule_registry
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_rules_by_ids(rule_ids: List[str]) -> List[Dict[str, Any]]:
        if not rule_ids:
            return []
        placeholders = ",".join(["?"] * len(rule_ids))
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT rule_id, description, parameter, operator, threshold_value,
                       scope_programmes, scope_batches, effective_from, effective_to,
                       source_doc_id, source_section
                FROM rule_registry
                WHERE rule_id IN ({placeholders})
                """,
                tuple(rule_ids)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
