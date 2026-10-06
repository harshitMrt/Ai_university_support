"""
Pytest fixtures and configuration.
Ensures clean database and ChromaDB setup before tests run.
"""

import pytest
from app.db.database import init_db
from app.db.seed import seed_database
from app.rag.ingest import ingest_all_documents
from app.rag.retriever import get_collection_count


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the database and ChromaDB collection before running tests."""
    init_db()
    seed_database()
    if get_collection_count() == 0:
        ingest_all_documents()
