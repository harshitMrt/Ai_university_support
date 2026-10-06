"""
Unit tests for live document ingestion.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.rag.retriever import query_documents

client = TestClient(app)


def test_live_document_ingestion():
    test_content = (
        "SECTION 1: TEST INGESTION\n"
        "This is a newly ingested policy for Dean Innovation Awards.\n"
        "Students winning first prize get Rs 25000 prize grant.\n"
    )

    files = {
        "file": ("INNOVATION-2026.txt", test_content.encode("utf-8"), "text/plain")
    }
    data = {
        "doc_id": "INNOV-2026",
        "title": "Dean Innovation Grant Rules 2026",
        "authority_level": 2,
        "doc_type": "Policy",
        "version": "1.0",
        "effective_from": "2026-10-06"
    }

    resp = client.post("/ingest", files=files, data=data)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["doc_id"] == "INNOV-2026"
    assert res_data["chunks_created"] >= 1
    assert res_data["embedding_status"] == "SUCCESS"

    # Verify query immediately finds the newly ingested document
    chunks = query_documents("Dean Innovation Awards grant prize", top_k=2)
    assert any(c["metadata"].get("doc_id") == "INNOV-2026" for c in chunks)
