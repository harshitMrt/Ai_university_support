"""
Unit tests for Authoritative Source Precedence and Conflict Resolution.
"""

from app.rules.source_precedence import resolve_authoritative_sources


def test_explicit_supersession():
    candidate_docs = [
        {
            "doc_id": "ACAD-REG-2021",
            "title": "Academic Regulations v2.0 (Archived)",
            "authority_level": 1,
            "version": "2.0",
            "effective_from": "2021-07-01",
            "effective_to": "2024-06-30",
            "supersedes": ""
        },
        {
            "doc_id": "ACAD-REG-2024",
            "title": "Academic Regulations v3.1",
            "authority_level": 1,
            "version": "3.1",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "supersedes": "ACAD-REG-2021"
        }
    ]

    res = resolve_authoritative_sources(candidate_docs, {"as_of_date": "2026-10-06"})
    assert res["selected_source"]["doc_id"] == "ACAD-REG-2024"
    assert any(e["doc_id"] == "ACAD-REG-2021" for e in res["excluded_sources"])


def test_higher_authority_wins():
    candidate_docs = [
        {
            "doc_id": "REG-01",
            "title": "Statutory Regulation",
            "authority_level": 1,
            "version": "1.0",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "supersedes": ""
        },
        {
            "doc_id": "NOTICE-01",
            "title": "Department Notice",
            "authority_level": 3,
            "version": "1.0",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "supersedes": ""
        }
    ]

    res = resolve_authoritative_sources(candidate_docs, {"as_of_date": "2026-10-06"})
    assert res["selected_source"]["doc_id"] == "REG-01"


def test_untrusted_level_5_excluded():
    candidate_docs = [
        {
            "doc_id": "OFFICIAL-POL",
            "title": "Official Policy",
            "authority_level": 2,
            "version": "1.0",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "supersedes": ""
        },
        {
            "doc_id": "UNOFF-FORUM",
            "title": "Student Forum Rumors",
            "authority_level": 5,
            "version": "0.1",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "supersedes": ""
        }
    ]

    res = resolve_authoritative_sources(candidate_docs, {"as_of_date": "2026-10-06"})
    assert res["selected_source"]["doc_id"] == "OFFICIAL-POL"
    assert any(e["doc_id"] == "UNOFF-FORUM" and "Untrusted" in e["reason"] for e in res["excluded_sources"])


def test_conflict_flagged_on_unresolvable_contention():
    candidate_docs = [
        {
            "doc_id": "COUNCIL-A",
            "title": "Equal Authority Ordinance A",
            "authority_level": 1,
            "version": "1.0",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "topic": "examination_fee",
            "supersedes": ""
        },
        {
            "doc_id": "COUNCIL-B",
            "title": "Equal Authority Ordinance B",
            "authority_level": 1,
            "version": "1.0",
            "effective_from": "2024-07-01",
            "effective_to": "",
            "topic": "examination_fee",
            "supersedes": ""
        }
    ]

    res = resolve_authoritative_sources(candidate_docs, {"as_of_date": "2026-10-06"})
    assert res["conflict_status"] is True
