from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.models.core_models import Base
from api.dependencies import engine, SessionLocal
from constants import settings


def _init_db():
    """Create all tables (SQLite dev) or ensure they exist (Postgres managed via Alembic)."""
    Base.metadata.create_all(bind=engine)


def _seed_db():
    """Insert synthetic Phase-1 identities so FK constraints pass."""
    from core.seed import seed_synthetic_data
    db = SessionLocal()
    try:
        seed_synthetic_data(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the first request, cleanup on shutdown."""
    import os
    if not os.environ.get("TESTING"):
        # In test mode the conftest manages DB setup — skip to avoid
        # seeding against the wrong engine or double-seeding.
        _init_db()
        _seed_db()
    yield  # Application runs here
    # Shutdown hooks go here if needed


app = FastAPI(
    title="Verilab OCR Lab-Report Consultation API",
    description="Backend API for managing lab reports, OCR extractions, and clinical reviews.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — origins driven by settings (wildcard only in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "Verilab backend is running",
        "environment": settings.environment,
        "db": settings.database_url.split("://")[0],  # e.g. "sqlite" or "postgresql"
    }


# Routers
from api.routers import intake, review, consultation, auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(intake.router)
app.include_router(review.router)
app.include_router(consultation.router)


