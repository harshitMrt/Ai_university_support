"""
Main FastAPI Application Entrypoint.
Connects all API routers, middleware, startup checks, and global exception handlers.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import UniversityAppException
from app.api.ask import router as ask_router
from app.api.ingest import router as ingest_router
from app.api.health import router as health_router
from app.api.audit import router as audit_router
from app.api.sources import router as sources_router
from app.api.student import router as student_router
from app.database.connection import init_db
from app.db.seed import seed_database
from app.rag.retriever import get_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure SQLite tables exist & seed if empty
    init_db()
    try:
        from app.repositories.student_repository import StudentRepository
        if not StudentRepository.get_by_id("S1001"):
            logger.info("Initial startup: Seeding synthetic student database...")
            seed_database()
    except Exception as e:
        logger.warning(f"Database check/seed warning: {e}")

    # Ensure ChromaDB collection is initialized
    try:
        get_collection()
    except Exception as e:
        logger.warning(f"ChromaDB check warning: {e}")

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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000.0, 2)
    response.headers["X-Response-Time-Ms"] = str(process_time)
    return response


@app.exception_handler(UniversityAppException)
async def domain_exception_handler(request: Request, exc: UniversityAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "detail": exc.detail
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
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
