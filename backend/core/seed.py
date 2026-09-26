"""
Synthetic-data seeder for Phase 1 local development.

Creates the stable tenant and user rows referenced by SYNTH_* constants in
constants.py so that foreign-key constraints are satisfied when running against
PostgreSQL (SQLite ignores FK constraints by default, but Postgres enforces them).

Called from main.py startup. Is a no-op if the rows already exist (idempotent).

Dev credentials (all roles): password = dev123
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from constants import (
    SYNTH_TENANT_ID,
    SYNTH_UPLOADER_ID,
    SYNTH_REVIEWER_ID,
    SYNTH_DOCTOR_ID,
    SYNTH_TENANT_NAME,
)
from core.security import get_password_hash
from db.models.core_models import Tenant, User

# Dev password for all Phase-1 synthetic users — set at first call, not at import time
# to avoid crashing if passlib/bcrypt aren't available during early imports.
_DEV_PASSWORD: str = "dev123"


def seed_synthetic_data(db: Session) -> None:
    """Idempotently create Phase-1 synthetic identities."""

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
    _ensure_user(db, SYNTH_UPLOADER_ID, "uploader@synth.verilab", "uploader")
    _ensure_user(db, SYNTH_REVIEWER_ID, "reviewer@synth.verilab", "reviewer")
    _ensure_user(db, SYNTH_DOCTOR_ID,   "doctor@synth.verilab",   "doctor")

    db.commit()


def _ensure_user(db: Session, user_id, email: str, role: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        user = User(id=user_id)
        db.add(user)

    # Keep local synthetic accounts usable when an old dev database is reused.
    user.tenant_id = SYNTH_TENANT_ID
    user.email = email
    user.hashed_password = get_password_hash(_DEV_PASSWORD)
    user.role = role
    user.mfa_enabled = False
    user.status = "active"
    db.flush()

