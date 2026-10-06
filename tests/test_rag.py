"""
Tests for RAG pipeline, chunking, and citations.
"""

from app.rag.chunking import chunk_document
from app.rag.retriever import query_documents, get_collection_count
from app.rag.citations import format_citation, deduplicate_citations


def test_chunking_metadata_retention():
    sample_text = (
        "SECTION 1: TITLE\n"
        "This is an official regulation.\n\n"
        "SECTION 4: ATTENDANCE\n"
        "Students must maintain 75% attendance.\n"
    )
    base_meta = {
        "doc_id": "TEST-REG-2024",
        "title": "Test Regulations",
        "issuer": "Academic Council",
        "authority_level": 1,
        "doc_type": "Regulation",
        "version": "1.0",
        "effective_from": "2024-07-01",
        "effective_to": "",
        "supersedes": "",
        "scope_programmes": "ALL",
        "scope_batches": "ALL",
        "provenance": "Unit Test",
        "retrieved_on": "2026-10-06",
        "synthetic": "TRUE"
    }

    chunks = chunk_document(sample_text, base_meta)
    assert len(chunks) >= 1
    chunk = chunks[0]
    meta = chunk["metadata"]

    required_keys = [
        "doc_id", "title", "issuer", "authority_level", "doc_type",
        "version", "effective_from", "effective_to", "supersedes",
        "scope_programmes", "scope_batches", "provenance", "retrieved_on", "synthetic",
        "section", "page"
    ]
    for k in required_keys:
        assert k in meta, f"Missing required metadata key: {k}"


def test_retriever_query():
    assert get_collection_count() > 0
    results = query_documents("What is the minimum attendance required?", top_k=3)
    assert len(results) > 0
    assert any("ACAD-REG" in r["metadata"].get("doc_id", "") or "ATT-POL" in r["metadata"].get("doc_id", "") for r in results)


def test_citations_formatting():
    meta = {
        "title": "Academic Regulations for B.Tech",
        "section": "Section 7.3",
        "page": 2,
        "version": "3.1",
        "effective_from": "2024-07-01",
        "doc_id": "ACAD-REG-2024",
        "authority_level": 1
    }
    cit = format_citation(meta)
    assert cit["title"] == "Academic Regulations for B.Tech"
    assert cit["section"] == "Section 7.3"
    assert cit["version"] == "3.1"
    assert cit["doc_id"] == "ACAD-REG-2024"

    deduped = deduplicate_citations([cit, cit])
    assert len(deduped) == 1
