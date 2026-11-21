"""
Synthetic-data seeder for Phase 1 local development.

Creates the stable tenant and user rows referenced by SYNTH_* constants in
constants.py so that foreign-key constraints are satisfied when running against
PostgreSQL (SQLite ignores FK constraints by default, but Postgres enforces them).

Called from main.py startup. Is a no-op if the rows already exist (idempotent).

Dev credentials (all roles): password = dev123 in development only.
Outside development the password comes from DEMO_USER_PASSWORD; if that is
unset, no users are seeded at all.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from constants import (
    settings,
    SYNTH_TENANT_ID,
    SYNTH_UPLOADER_ID,
    SYNTH_REVIEWER_ID,
    SYNTH_DOCTOR_ID,
    SYNTH_ADMIN_ID,
    SYNTH_TENANT_NAME,
)
from core.security import get_password_hash
from db.models.core_models import Tenant, User

# Dev password for all Phase-1 synthetic users — set at first call, not at import time
# to avoid crashing if passlib/bcrypt aren't available during early imports.
_DEV_PASSWORD: str = "dev123"

logger = logging.getLogger(__name__)


def _seed_password() -> str | None:
    if settings.demo_user_password:
        return settings.demo_user_password
    if settings.environment == "development":
        return _DEV_PASSWORD
    return None


def seed_synthetic_data(db: Session) -> None:
    """Idempotently create Phase-1 synthetic identities."""
    password = _seed_password()
    if password is None:
        logger.warning("DEMO_USER_PASSWORD is not set; skipping synthetic user seeding.")
        return

    # 1. Tenant
    if not db.query(Tenant).filter(Tenant.id == SYNTH_TENANT_ID).first():
        db.add(Tenant(
            id=SYNTH_TENANT_ID,
            name=SYNTH_TENANT_NAME,
            data_residency_region="in-mumbai",
            status="active",
        ))
        db.flush()

    # 2. Users — one per Phase-1 persona
    password_hash = get_password_hash(password)
    _ensure_user(db, SYNTH_UPLOADER_ID, "uploader@synth.verilab", "uploader", password_hash)
    _ensure_user(db, SYNTH_REVIEWER_ID, "reviewer@synth.verilab", "reviewer", password_hash)
    _ensure_user(db, SYNTH_DOCTOR_ID,   "doctor@synth.verilab",   "doctor", password_hash)
    _ensure_user(db, SYNTH_ADMIN_ID,    "admin@synth.verilab",    "admin", password_hash)

    db.commit()


def _ensure_user(db: Session, user_id, email: str, role: str, password_hash: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        user = User(id=user_id)
        db.add(user)

    # Keep local synthetic accounts usable when an old dev database is reused.
    user.tenant_id = SYNTH_TENANT_ID
    user.email = email
    user.hashed_password = password_hash
    user.role = role
    user.mfa_enabled = False
    user.status = "active"
    db.flush()

