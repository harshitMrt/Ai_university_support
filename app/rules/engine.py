"""
Generic Deterministic Rule Engine.
Evaluates rules stored dynamically in SQLite rule_registry against student and academic context.
Operators supported: >=, <=, >, <, ==, !=
"""

import operator
from typing import Any, Dict, List, Optional
from app.db.database import get_connection

OPERATOR_MAP = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
    "=": operator.eq,
}


def fetch_applicable_rules(
    rule_ids: Optional[List[str]] = None,
    programme: Optional[str] = None,
    batch_year: Optional[int] = None,
    as_of_date: Optional[str] = "2026-10-06"
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT rule_id, description, parameter, operator, threshold_value,
           scope_programmes, scope_batches, effective_from, effective_to,
           source_doc_id, source_section
    FROM rule_registry
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    applicable = []
    for r in rows:
        rid = r["rule_id"]
        if rule_ids and rid not in rule_ids:
            continue

        # Check effective date
        eff_from = r["effective_from"]
        eff_to = r["effective_to"]
        if as_of_date:
            if eff_from and as_of_date < eff_from:
                continue
            if eff_to and as_of_date > eff_to:
                continue

        # Check scope
        scope_p = r["scope_programmes"]
        if programme and scope_p != "ALL" and programme.lower() not in scope_p.lower():
            continue

        scope_b = str(r["scope_batches"])
        if batch_year and scope_b != "ALL" and str(batch_year) not in scope_b:
            continue

        applicable.append(dict(r))

    return applicable


def evaluate_single_rule(
    rule: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    param_name = rule["parameter"]
    op_str = rule["operator"].strip()
    threshold = float(rule["threshold_value"]) if rule["threshold_value"] is not None else 0.0

    actual_val = context.get(param_name)
    if actual_val is None:
        return {
            "rule_id": rule["rule_id"],
            "description": rule["description"],
            "parameter": param_name,
            "operator": op_str,
            "threshold": threshold,
            "actual_value": None,
            "passed": False,
            "reason": f"Required parameter '{param_name}' not available in student context."
        }

    actual_val = float(actual_val)
    op_fn = OPERATOR_MAP.get(op_str)
    if not op_fn:
        return {
            "rule_id": rule["rule_id"],
            "description": rule["description"],
            "parameter": param_name,
            "operator": op_str,
            "threshold": threshold,
            "actual_value": actual_val,
            "passed": False,
            "reason": f"Unsupported operator '{op_str}'."
        }

    passed = op_fn(actual_val, threshold)

    return {
        "rule_id": rule["rule_id"],
        "description": rule["description"],
        "parameter": param_name,
        "operator": op_str,
        "threshold": threshold,
        "actual_value": actual_val,
        "passed": bool(passed),
        "source_doc_id": rule.get("source_doc_id"),
        "source_section": rule.get("source_section"),
        "reason": f"{param_name} ({actual_val}) {op_str} {threshold} is {'SATISFIED' if passed else 'VIOLATED'}."
    }
