"""
Authoritative Source Precedence and Conflict Resolution Module.
Implements the exact hierarchy and resolution rules:
Authority Levels:
1 = Statutes, Ordinances, Academic Regulations (Highest)
2 = Official circulars, Notifications, Authorised office documents
3 = Department notices
4 = Handbooks, FAQs
5 = Unofficial content (Untrusted)

Resolution Rules:
1. Prefer documents that are currently effective.
2. Prefer documents whose scope matches the student/program/batch.
3. An explicit supersession relationship overrides an older document.
4. Higher authority overrides lower authority (lower numerical authority_level).
5. More recent effective document wins when authority is otherwise equal.
6. If conflict cannot be safely resolved, return conflict_status = True ("conflict_flagged").
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def resolve_authoritative_sources(
    candidate_documents: List[Dict[str, Any]],
    student_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates candidate documents according to authoritative source precedence.

    Returns a dictionary containing:
    - selected_source: Dict or None
    - candidate_sources: List of remaining valid sources
    - excluded_sources: List of excluded documents with reasons
    - reason: Human-readable explanation of why the source was selected
    - conflict_status: bool (True if unresolvable conflict exists)
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

    # Map for quick lookup of supersessions
    superseded_doc_ids = set()
    for doc in candidate_documents:
        supersedes_target = doc.get("supersedes")
        if supersedes_target and supersedes_target.strip():
            superseded_doc_ids.add(supersedes_target.strip())

    # Step 1: Filter untrusted level 5 sources if authoritative sources exist
    has_trusted = any(int(d.get("authority_level", 5)) <= 4 for d in candidate_documents)

    for doc in candidate_documents:
        doc_id = doc.get("doc_id", "UNKNOWN")
        auth_level = int(doc.get("authority_level", 5))

        # Check untrusted level 5
        if auth_level >= 5 and has_trusted:
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": "Untrusted source (Authority Level 5) excluded in favor of official sources."
            })
            continue

        # Check explicit supersession
        if doc_id in superseded_doc_ids:
            # Find the superseding doc
            superseding = [d for d in candidate_documents if d.get("supersedes") == doc_id]
            superseding_title = superseding[0].get("title", superseding[0].get("doc_id")) if superseding else "a newer regulation"
            excluded_sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "authority_level": auth_level,
                "reason": f"Superseded by {superseding_title} (explicit supersession)."
            })
            continue

        # Check effective dates
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

        # Check scope mismatch
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

    # Step 2: Sort candidates according to source precedence:
    # 1. Authority level ascending (1 is best, 5 is worst)
    # 2. Scope specificity (matching specific programme/batch before "ALL")
    # 3. Effective date descending (most recently enacted document wins)
    # 4. Version descending
    def sort_key(d: Dict[str, Any]) -> Tuple[int, int, float, float]:
        auth = int(d.get("authority_level", 5))
        is_specific_prog = 0 if (student_programme and student_programme.lower() in d.get("scope_programmes", "").lower()) else 1
        eff_from = parse_date(d.get("effective_from"))
        eff_timestamp = -eff_from.timestamp() if eff_from else 0.0
        try:
            ver = -float(str(d.get("version", "1.0")).replace("v", ""))
        except ValueError:
            ver = 0.0
        return (auth, is_specific_prog, eff_timestamp, ver)

    active_candidates.sort(key=sort_key)

    # Check for unresolvable conflict among top-level candidates
    # If two candidates have the same highest authority, same scope, same effective date, but different doc_ids and content
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
            # Check if they have potentially conflicting values for same topic
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
