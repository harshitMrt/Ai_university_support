"""
Generic Deterministic Rule Engine for University Regulations.

Purpose:
--------
Evaluates dynamic institutional policy rules stored in SQLite (table: `rule_registry`)
against real-time student academic metrics (attendance %, CGPA, backlogs, marks).

Key Features:
-------------
1. Temporal Validation: Verifies that rules are active as of a specific date (`effective_from` <= date <= `effective_to`).
2. Scope Matching: Restricts rule applicability by academic programme (e.g. 'B.Tech CSE') and batch year.
3. Deterministic Evaluation: Avoids LLM hallucination for mathematical criteria by computing exact logical comparisons.
4. Supported Comparison Operators: >=, <=, >, <, ==, !=, =.
5. Traceability: Retains exact `source_doc_id` and `source_section` citations for auditability.
"""

import operator
from typing import Any, Dict, List, Optional
from app.db.database import get_connection

# Mapping mathematical string operator representations to standard Python operator functions
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
    """
    Queries the SQLite rule_registry table and filters rules matching the given execution context.

    Parameters:
    -----------
    rule_ids : Optional[List[str]]
        Specific rule identifiers to fetch (e.g. ['ATT-MIN-01', 'SUPP-ELIG-ATT']).
        If None, all active rules are evaluated.
    programme : Optional[str]
        The student's enrolled programme (e.g. 'B.Tech CSE'). Used for scope matching.
    batch_year : Optional[int]
        The student's admission year (e.g. 2023). Used for cohort-specific policies.
    as_of_date : Optional[str]
        ISO-8601 date string (YYYY-MM-DD) representing the point in time for evaluation.

    Returns:
    --------
    List[Dict[str, Any]]:
        List of matching rule dictionaries ready for evaluation.
    """
    # Establish read-only connection to university database
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

        # 1. Filter by explicit Rule IDs if requested
        if rule_ids and rid not in rule_ids:
            continue

        # 2. Temporal validation: Ensure policy is effective as of the query date
        eff_from = r["effective_from"]
        eff_to = r["effective_to"]
        if as_of_date:
            # Rule has not yet come into effect
            if eff_from and as_of_date < eff_from:
                continue
            # Rule has expired or been retired
            if eff_to and as_of_date > eff_to:
                continue

        # 3. Scope validation: Programme level (e.g., 'B.Tech CSE' vs 'ALL')
        scope_p = r["scope_programmes"]
        if programme and scope_p != "ALL" and programme.lower() not in scope_p.lower():
            continue

        # 4. Scope validation: Batch cohort level (e.g., 2023 vs 'ALL')
        scope_b = str(r["scope_batches"])
        if batch_year and scope_b != "ALL" and str(batch_year) not in scope_b:
            continue

        # Rule satisfies all contextual constraints
        applicable.append(dict(r))

    return applicable


def evaluate_single_rule(
    rule: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministically evaluates an individual policy threshold against a student's context values.

    Parameters:
    -----------
    rule : Dict[str, Any]
        Rule metadata containing 'parameter', 'operator', and 'threshold_value'.
    context : Dict[str, Any]
        Dictionary of student metric values, e.g. {'attendance_percentage': 75.0, 'cgpa': 8.5}.

    Returns:
    --------
    Dict[str, Any]:
        Evaluation result containing pass/fail flag, comparison details, and regulatory citations.
    """
    param_name = rule["parameter"]
    op_str = rule["operator"].strip()
    threshold = float(rule["threshold_value"]) if rule["threshold_value"] is not None else 0.0

    # Retrieve current student metric value
    actual_val = context.get(param_name)

    # Handle missing student metric
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

    # Handle unsupported operator edge-case safely
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

    # Perform exact mathematical/logical evaluation
    passed = op_fn(actual_val, threshold)

    # Return structured verifiable evaluation artifact
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
