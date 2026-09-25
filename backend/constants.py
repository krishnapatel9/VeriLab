"""Phase 1 seed identities, hard-coded consultation test list, and app settings.

The test list is configuration-shaped (a named, version-labeled list) but not
yet the Phase 2 Rules Service. Do not infer tests from free text.
"""

from __future__ import annotations

import uuid
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    All values have safe defaults so the app runs without a .env (SQLite dev mode).
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database — defaults to SQLite for fast local dev (no Docker needed)
    database_url: str = "sqlite:///./verilab_dev.db"

    # Security — MUST be changed for staging/production
    secret_key: str = "dev_only_insecure_secret_key_change_before_staging"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # CORS — comma-separated origins
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Upload limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # OCR provider: "mock" | "textract"
    ocr_provider: str = "mock"

    # Notification provider: "mock" | "ses" | "msg91"
    notification_provider: str = "mock"

    environment: str = "development"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


# Module-level singleton — import settings from here, not re-instantiate
settings = Settings()

# ---------------------------------------------------------------------------
# Stable synthetic IDs (Phase 1 only — replaced by real auth in Phase 2)
# ---------------------------------------------------------------------------
SYNTH_TENANT_ID  = uuid.UUID("00000000-0000-4000-8000-000000000001")
SYNTH_UPLOADER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
SYNTH_REVIEWER_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")
SYNTH_DOCTOR_ID   = uuid.UUID("00000000-0000-4000-8000-000000000004")

SYNTH_TENANT_NAME = "SYNTH-Clinic-001"
PHASE1_CONSULTATION_TYPE_NAME = "Phase1 General Consultation"
PHASE1_RULE_VERSION = 1

# Hard-coded selected tests for Sprint 4. Unlisted extracted tests must still
# be stored and disclosed as additional results (FR-24 / FR-27).
PHASE1_SELECTED_TEST_NAMES = ("Hemoglobin",)

MAX_UPLOAD_BYTES = settings.max_upload_bytes
ALLOWED_UPLOAD_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg")

# Phase 1 routing only — not a production clinical threshold. Field-specific
# configurable thresholds belong in the Rules/Config layer (Phase 2 / FR-17).
PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW = 0.90

