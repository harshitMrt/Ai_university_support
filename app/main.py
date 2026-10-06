"""
Main FastAPI Application Entrypoint.
Connects all API routers, middleware, and startup checks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.ask import router as ask_router
from app.api.ingest import router as ingest_router
from app.api.health import router as health_router
from app.api.audit import router as audit_router
from app.api.sources import router as sources_router
from app.api.student import router as student_router
from app.db.database import init_db
from app.db.seed import seed_database
from app.rag.ingest import ingest_all_documents
from app.rag.retriever import get_collection_count


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure SQLite tables exist & seed if empty
    init_db()
    try:
        from app.tools.student import get_student
        if not get_student("S1001"):
            print("Initial startup: Seeding synthetic student database...")
            seed_database()
    except Exception as e:
        print(f"Database check/seed warning: {e}")

    # Ensure ChromaDB has documents indexed
    try:
        if get_collection_count() == 0:
            print("Initial startup: Ingesting university documents into ChromaDB...")
            ingest_all_documents()
    except Exception as e:
        print(f"ChromaDB check warning: {e}")

    yield


app = FastAPI(
    title="AI-Powered University Student Services Assistant",
    description="Grounded, authoritative, deterministic student services assistant built for HCLTech Hackathon.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler to never expose raw stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request. Please contact student services if this persists.",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )

# Include all API routers
app.include_router(health_router)
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(audit_router)
app.include_router(sources_router)
app.include_router(student_router)


@app.get("/")
async def root():
    return {
        "service": "AI-Powered University Student Services Assistant",
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
        "ask_url": "/ask"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
