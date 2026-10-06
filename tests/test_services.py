"""
Unit tests for domain services (eligibility, source resolution, citations, grounding).
"""

from app.services.citation import format_citation, format_citation_string, deduplicate_citations
from app.services.grounding import verify_query_presence, validate_grounding, CANONICAL_NOT_FOUND_MESSAGE
from app.services.source_resolution import resolve_authoritative_sources, parse_date
from app.services.eligibility_service import check_exam_eligibility, evaluate_single_rule, fetch_applicable_rules


def test_parse_date_valid_and_invalid():
    assert parse_date("2026-10-06") is not None
    assert parse_date("invalid-date") is None
    assert parse_date("") is None
    assert parse_date(None) is None


def test_citation_service_formatting():
    meta = {
        "title": "Academic Regulations",
        "section": "Section 4.1",
        "page": 3,
        "version": "3.1",
        "effective_from": "2024-07-01",
        "doc_id": "ACAD-REG-2024",
        "authority_level": 1
    }
    cit = format_citation(meta)
    assert cit["title"] == "Academic Regulations"
    assert cit["doc_id"] == "ACAD-REG-2024"
    assert cit["authority_level"] == 1

    cit_str = format_citation_string(cit)
    assert "ACAD-REG-2024" in cit_str
    assert "Section 4.1" in cit_str

    deduped = deduplicate_citations([cit, cit])
    assert len(deduped) == 1


def test_grounding_service_verification():
    chunks = [
        {"text": "Students must attend at least 75 percent of all scheduled classes.", "metadata": {"title": "Attendance Policy", "section": "Section 2"}}
    ]
    assert verify_query_presence("What is the attendance threshold?", chunks) is True
    assert verify_query_presence("What is the fee for swimming pool membership?", chunks) is False


def test_grounding_service_canonical_fallback():
    state = {
        "answer_type": "not_found",
        "answer": "Something not found",
        "citations": [{"doc_id": "DOC1"}]
    }
    validated = validate_grounding(state)
    assert validated["answer_type"] == "not_found"
    assert validated["answer"] == CANONICAL_NOT_FOUND_MESSAGE
    assert validated["citations"] == []


def test_eligibility_service_rule_evaluation():
    rule = {
        "rule_id": "TEST-RULE",
        "description": "Attendance >= 75%",
        "parameter": "attendance_percentage",
        "operator": ">=",
        "threshold_value": 75.0,
        "source_doc_id": "DOC1",
        "source_section": "SEC1"
    }
    res_pass = evaluate_single_rule(rule, {"attendance_percentage": 80.0})
    assert res_pass["passed"] is True

    res_fail = evaluate_single_rule(rule, {"attendance_percentage": 70.0})
    assert res_fail["passed"] is False
