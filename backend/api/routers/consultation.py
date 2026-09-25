"""
Consultation router — the doctor-facing view.

Sprint 4 (Phase 1): applies the hard-coded PHASE1_SELECTED_TEST_NAMES filter.
Sprint 7 (Phase 2): will replace this with the Rules Service query.

Key invariants enforced here:
- Only verified results appear in selected_results (FR-24 safety rule).
- All other extracted results are returned in additional_results and MUST be
  disclosed to the client (FR-27).
- Critical results are ALWAYS included in selected_results regardless of
  the test-name filter (FR-33 / critical-flag surfacing gate).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db, require_role
from core.audit import emit_audit_event
from db.models.core_models import Report, Result, User
from schemas.consultation import ConsultationResponse, ConsultationResultItem
from constants import (
    PHASE1_SELECTED_TEST_NAMES,
    PHASE1_CONSULTATION_TYPE_NAME,
    PHASE1_RULE_VERSION,
)

router = APIRouter(prefix="/api/v1/consultation", tags=["Consultation"])

# Statuses that are safe to show to a doctor (verified by a clinical reviewer)
_VERIFIED_STATUSES = {"verified_as_reported", "verified_with_correction"}


@router.get("/{report_id}", response_model=ConsultationResponse)
def get_consultation_view(
    report_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """
    Assembles the doctor-facing consultation view for a report.

    Returns:
      selected_results   — tests matching the active consultation type,
                           restricted to verified results only.
      additional_results — all remaining extracted results (disclosed per FR-27),
                           also restricted to verified.

    Critical results (is_critical=True) bypass the test-name filter and are
    always included in selected_results (FR-33).
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Only include results that have been verified
    all_results = (
        db.query(Result)
        .filter(
            Result.report_id == report_id,
            Result.verification_status.in_(_VERIFIED_STATUSES),
        )
        .all()
    )

    # Partition into selected vs. additional (FR-24, FR-27)
    selected: list[Result] = []
    additional: list[Result] = []

    for r in all_results:
        name = (r.test_name_raw or "").strip()
        is_in_consultation = any(
            name.lower() == sel.lower() for sel in PHASE1_SELECTED_TEST_NAMES
        )
        # Critical results always appear in selected regardless of filter (FR-33)
        if is_in_consultation or r.is_critical:
            selected.append(r)
        else:
            additional.append(r)

    # Audit: doctor opened the consultation view
    emit_audit_event(
        db=db,
        event_type="consultation.viewed",
        resource_type="report",
        resource_id=report_id,
        metadata={
            "rule_version": PHASE1_RULE_VERSION,
            "consultation_type": PHASE1_CONSULTATION_TYPE_NAME,
            "selected_count": len(selected),
            "additional_count": len(additional),
        },
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()  # Persist the audit event

    def _to_schema(r: Result) -> ConsultationResultItem:
        return ConsultationResultItem(
            id=r.id,
            test_name_raw=r.test_name_raw or "",
            value_raw=r.value_raw or "",
            unit_raw=r.unit_raw,
            reference_range_raw=r.reference_range_raw,
            flag_raw=r.flag_raw,
            is_critical=r.is_critical,
            verification_status=r.verification_status,
            source_page=r.source_page,
            source_x=float(r.source_x),
            source_y=float(r.source_y),
            source_width=float(r.source_width),
            source_height=float(r.source_height),
        )

    return ConsultationResponse(
        report_id=report.id,
        report_status=report.status,
        rule_version=PHASE1_RULE_VERSION,
        consultation_type=PHASE1_CONSULTATION_TYPE_NAME,
        selected_results=[_to_schema(r) for r in selected],
        additional_results=[_to_schema(r) for r in additional],
    )
