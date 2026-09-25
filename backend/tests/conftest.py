"""
Pytest fixtures for all Verilab backend tests.

Uses a file-based SQLite database (per-session temp file) so the same
in-memory state persists across the session. Tables are created ONCE,
seed data is inserted ONCE, and tests clean up after themselves using
explicit delete-after patterns.

Why not drop_all/create_all per test?
- In-memory SQLite loses data when a connection closes.
- Creating a new engine per test risks double-seeding on reconnect.
The simplest correct pattern for this project: session-scoped engine,
per-function session with explicit cleanup.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from db.models.core_models import Base
from api.dependencies import get_db

# ── Shared engine for the whole test session ─────────────────────────────────
# Use a named on-disk temp file so in-memory state isn't lost between sessions.
TEST_DATABASE_URL = "sqlite:///./verilab_test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Dependency override: route API requests to the test engine."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the whole test session, then drop on teardown."""
    Base.metadata.drop_all(bind=test_engine)   # Start clean
    Base.metadata.create_all(bind=test_engine)

    # Seed synthetic identities once
    db = TestSessionLocal()
    try:
        from core.seed import seed_synthetic_data
        seed_synthetic_data(db)
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(setup_database):
    """
    Provide a DB session for the test. The session is closed after the test.
    Data written by a test WILL persist to subsequent tests in the same session —
    use unique identifiers in test data to avoid collisions.
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(setup_database):
    """
    FastAPI TestClient with the DB dependency overridden to use the test engine.
    """
    import os
    os.environ["TESTING"] = "1"  # Signal to lifespan to skip seeder

    from main import app
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    os.environ.pop("TESTING", None)
