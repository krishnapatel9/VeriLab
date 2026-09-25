from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, ForeignKey, JSON, Text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid  # SQLAlchemy 2.0 dialect-agnostic UUID

# Only import PostgreSQL dialect types for runtime use on Postgres;
# tests use SQLite so we must NOT use postgresql.UUID or JSONB as column types.

Base = declarative_base()


def generate_uuidv7() -> uuid.UUID:
    """
    Returns a new UUID. Phase 1 uses uuid4 as a placeholder.
    Phase 2 migration to UUIDv7 (time-ordered) will replace this call.
    """
    return uuid.uuid4()


class Tenant(Base):
    __tablename__ = 'tenants'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    name: Mapped[str] = mapped_column(String, nullable=False)
    data_residency_region: Mapped[str] = mapped_column(String, default="in-mumbai")
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="tenant")
    patients = relationship("Patient", back_populates="tenant")


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('tenants.id'), nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False, default="")
    role: Mapped[str] = mapped_column(String, nullable=False)  # uploader / reviewer / doctor / clinical_admin / audit_admin / tenant_owner
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")


class Patient(Base):
    __tablename__ = 'patients'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('tenants.id'), nullable=False)
    external_patient_id: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="patients")
    reports = relationship("Report", back_populates="patient")


class Report(Base):
    __tablename__ = 'reports'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('tenants.id'), nullable=False)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('patients.id'), nullable=True)
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    file_object_key: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # intake_pending, processing, processed, error
    report_status_extracted: Mapped[str] = mapped_column(String, nullable=False)  # final, preliminary, unknown
    lab_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    report_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    collection_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    match_status: Mapped[str] = mapped_column(String, nullable=False)  # unmatched, needs_review, confirmed, conflict
    superseded_by_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('reports.id'), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="reports")
    results = relationship("Result", back_populates="report")
    review_items = relationship("ReviewItem", back_populates="report")


class Result(Base):
    __tablename__ = 'results'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('tenants.id'), nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('reports.id'), nullable=False)
    test_name_raw: Mapped[str] = mapped_column(String, nullable=False)
    test_name_normalized: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    value_raw: Mapped[str] = mapped_column(String, nullable=False)
    value_numeric: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    unit_raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_range_raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    flag_raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_test_name: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    confidence_value: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    confidence_unit: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    confidence_reference_range: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)

    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_x: Mapped[float] = mapped_column(Numeric, nullable=False)
    source_y: Mapped[float] = mapped_column(Numeric, nullable=False)
    source_width: Mapped[float] = mapped_column(Numeric, nullable=False)
    source_height: Mapped[float] = mapped_column(Numeric, nullable=False)

    verification_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="results")
    corrections = relationship("ResultCorrection", back_populates="result")


class ResultCorrection(Base):
    __tablename__ = 'result_corrections'
    # Append-only table — rows MUST NOT be updated or deleted

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('results.id'), nullable=False)
    original_value_raw: Mapped[str] = mapped_column(String, nullable=False)
    corrected_value_raw: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)

    evidence_source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_source_x: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    evidence_source_y: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    evidence_source_width: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    evidence_source_height: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)

    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    result = relationship("Result", back_populates="corrections")


class ReviewItem(Base):
    __tablename__ = 'review_items'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('tenants.id'), nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('reports.id'), nullable=False)
    result_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('results.id'), nullable=True)
    item_type: Mapped[str] = mapped_column(String, nullable=False)  # field_confidence, patient_match, multi_report_detected
    flag_reason: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # open, resolved
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="review_items")


class AuditEvent(Base):
    __tablename__ = 'audit_events'
    # Append-only table for compliance — rows MUST NOT be updated or deleted

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=generate_uuidv7)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('tenants.id'), nullable=True)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    # resource_id is not a FK — it can reference any entity type
    resource_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    # JSON is portable (SQLite + Postgres); upgrade to JSONB via Alembic migration later
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    prev_event_hash: Mapped[str] = mapped_column(String, nullable=False)
    event_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
