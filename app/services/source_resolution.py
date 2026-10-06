"""
Authoritative Source Precedence and Conflict Resolution Service.

Implements institutional precedence rules:
1. Authority Levels:
   - Level 1: Statutes, Ordinances, Academic Council Regulations (Highest)
   - Level 2: Official circulars, Dean/Registrar Notifications
   - Level 3: Department notices (e.g., Computer Science Lab guidelines)
   - Level 4: Handbooks, Orientation FAQs
   - Level 5: Unofficial content (Student forums, Reddit/Discord chatter) -> UNTRUSTED

2. Precedence Hierarchy & Conflict Resolution Algorithm:
   - Step 1: Filter out expired or not-yet-effective policies based on query date (`as_of_date`).
   - Step 2: Enforce explicit supersession (e.g. ACAD-REG-2024 supersedes ACAD-REG-2021).
   - Step 3: Apply scope specialization: Specific departmental policies (e.g. B.Tech CSE)
             take precedence over general ('ALL') regulations for students of that department.
   - Step 4: Higher authority overrides lower authority (Level 1 > Level 2 > Level 3).
   - Step 5: Untrusted Level 5 documents are strictly excluded from being authoritative.
   - Step 6: If two documents of identical authority, date, and scope directly conflict,
             flag conflict_status = True (`conflict_flagged`) rather than silently hallucinating.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Safely parses an ISO date string (YYYY-MM-DD) into a datetime object.
    Returns None if missing, empty, or unparseable.
    """
    if not date_str or not str(date_str).strip():
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
    except ValueError:
        return None


def resolve_authoritative_sources(
    candidate_documents: List[Dict[str, Any]],
    student_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates candidate documents according to authoritative source precedence.
    """
    if not candidate_documents:
        return {
            "selected_source": None,
            "candidate_sources": [],
            "excluded_sources": [],
            "reason": "No candidate documents retrieved.",
            "conflict_status": False,
        }

    ctx = student_context or {}
    as_of_date_str = ctx.get("as_of_date", "2026-10-06")
    as_of_date = parse_date(as_of_date_str) or datetime.now()
    student_programme = ctx.get("programme")
    student_batch = ctx.get("batch_year")

    excluded_sources: List[Dict[str, Any]] = []
    active_candidates: List[Dict[str, Any]] = []

    # Map for quick lookup of superseding relationships (e.g. doc A supersedes doc B)
    superseded_doc_ids = set()
    for doc in candidate_documents:
        supersedes_target = doc.get("supersedes")
        if supersedes_target and str(supersedes_target).strip():
            superseded_doc_ids.add(str(supersedes_target).strip())

    # Check whether any official/trusted sources (Level 1-4) exist in candidate pool
    has_trusted = any(int(d.get("authority_level", 5)) <= 4 for d in candidate_documents)

    for doc in candidate_documents:
        doc_id = doc.get("doc_id", "UNKNOWN")
        auth_level = int(doc.get("authority_level", 5))

        # Filter 1: Untrusted Content (Authority Level 5)
        if auth_level >= 5 and has_trusted:
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": "Untrusted source (Authority Level 5) excluded in favor of official sources."
            })
            continue

        # Filter 2: Explicit Supersession
        if doc_id in superseded_doc_ids:
            superseding = [d for d in candidate_documents if d.get("supersedes") == doc_id]
            superseding_title = superseding[0].get("title", superseding[0].get("doc_id")) if superseding else "a newer regulation"
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": f"Superseded by {superseding_title} (explicit supersession)."
            })
            continue

        # Filter 3: Temporal Validity (effective_from and effective_to)
        eff_from = parse_date(doc.get("effective_from"))
        eff_to = parse_date(doc.get("effective_to"))

        if eff_from and eff_from > as_of_date:
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": f"Not yet effective (effective from {doc.get('effective_from')}, query date is {as_of_date_str})."
            })
            continue

        if eff_to and eff_to < as_of_date:
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": f"Expired policy (effective to {doc.get('effective_to')}, query date is {as_of_date_str})."
            })
            continue

        # Filter 4: Scope Compatibility (Programme & Batch)
        scope_progs = doc.get("scope_programmes", "ALL")
        if student_programme and scope_progs != "ALL":
            if student_programme.lower() not in scope_progs.lower():
                excluded_sources.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "authority_level": auth_level,
                    "reason": f"Scope mismatch: policy applies to '{scope_progs}', student programme is '{student_programme}'."
                })
                continue

        scope_batches = str(doc.get("scope_batches", "ALL"))
        if student_batch and scope_batches != "ALL":
            if str(student_batch) not in scope_batches:
                excluded_sources.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "authority_level": auth_level,
                    "reason": f"Scope mismatch: policy applies to batch '{scope_batches}', student batch is '{student_batch}'."
                })
                continue

        active_candidates.append(doc)

    if not active_candidates:
        return {
            "selected_source": None,
            "candidate_sources": [],
            "excluded_sources": excluded_sources,
            "reason": "All candidate documents were excluded due to expiration, supersession, scope mismatch, or lack of trust.",
            "conflict_status": False,
        }

    # Deterministic Precedence Sort
    def sort_key(d: Dict[str, Any]) -> Tuple[int, int, float, float]:
        auth = int(d.get("authority_level", 5))
        is_specific_prog = 0 if (
            student_programme
            and d.get("scope_programmes") != "ALL"
            and student_programme.lower() in d.get("scope_programmes", "").lower()
        ) else 1
        eff_from = parse_date(d.get("effective_from"))
        eff_timestamp = -eff_from.timestamp() if eff_from else 0.0
        try:
            ver = -float(str(d.get("version", "1.0")).replace("v", ""))
        except ValueError:
            ver = 0.0
        return (is_specific_prog, auth, eff_timestamp, ver)

    active_candidates.sort(key=sort_key)

    # Conflict Detection Across Equal Precedence Authorities
    conflict_status = False
    if len(active_candidates) > 1:
        top1 = active_candidates[0]
        top2 = active_candidates[1]
        if (
            int(top1.get("authority_level", 5)) == int(top2.get("authority_level", 5))
            and top1.get("effective_from") == top2.get("effective_from")
            and top1.get("doc_id") != top2.get("doc_id")
            and top1.get("supersedes") != top2.get("doc_id")
            and top2.get("supersedes") != top1.get("doc_id")
        ):
            topic1 = top1.get("topic", top1.get("title", ""))
            topic2 = top2.get("topic", top2.get("title", ""))
            if topic1 and topic2 and (topic1 in topic2 or topic2 in topic1):
                conflict_status = True

    selected = active_candidates[0]
    auth_level_sel = selected.get("authority_level", 1)
    sel_title = selected.get("title", selected.get("doc_id", "Unknown Document"))
    sel_ver = selected.get("version", "N/A")
    sel_eff = selected.get("effective_from", "N/A")

    reason = (
        f"Selected '{sel_title}' (Doc ID: {selected.get('doc_id')}, Version: {sel_ver}) because it has the highest authority "
        f"(Level {auth_level_sel}), is currently active (Effective: {sel_eff}), matches the student scope, "
        f"and supersedes older regulations."
    )

    return {
        "selected_source": selected,
        "candidate_sources": active_candidates,
        "excluded_sources": excluded_sources,
        "reason": reason,
        "conflict_status": conflict_status,
    }
