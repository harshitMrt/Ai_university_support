"""
Load and reset all synthetic university data and document embeddings.
Run this script to initialize or restore the demo environment for judging.
"""

from app.db.database import init_db
from app.db.seed import seed_database
from app.rag.ingest import ingest_all_documents


def main():
    print("Initializing SQLite Database...")
    init_db()
    
    print("Seeding synthetic students, courses, attendance, results, and rules...")
    counts = seed_database()
    print("Database seeding completed:", counts)

    print("Ingesting all official university documents into ChromaDB...")
    ingested = ingest_all_documents()
    print(f"Successfully ingested {len(ingested)} documents into ChromaDB vector store.")

    print("\nEnvironment initialization complete! Ready for live demonstrations.")


if __name__ == "__main__":
    main()
