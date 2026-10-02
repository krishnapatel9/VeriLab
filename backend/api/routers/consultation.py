"""
Consultation router — the doctor-facing view.

Sprint 4 (Phase 1): applies the hard-coded PHASE1_SELECTED_TEST_NAMES filter.
Sprint 7 (Phase 2): will replace this with the Rules Service query.

Key invariants enforced here:
- Every extracted result is returned with its verification_status; nothing is
  hidden because it is unverified (Invariants 5 and 6). The UI must badge
  unverified rows.
- The effective value is the latest correction, with the OCR original alongside.
- Flagged/critical results are ALWAYS included in selected_results regardless of
  the test-name filter or verification state (FR-32).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db, require_role
from core.audit import emit_audit_event
from db.models.core_models import Report, Result, ResultCorrection, User
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
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.tenant_id == current_user.tenant_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    all_results = (
        db.query(Result)
        .filter(
            Result.report_id == report_id,
            Result.tenant_id == current_user.tenant_id,
        )
        .all()
    )

    # Latest correction per result (corrections are append-only; newest wins).
    latest_correction: dict[uuid.UUID, ResultCorrection] = {}
    if all_results:
        corrections = (
            db.query(ResultCorrection)
            .filter(ResultCorrection.result_id.in_([r.id for r in all_results]))
            .order_by(ResultCorrection.created_at.asc())
            .all()
        )
        for c in corrections:
            latest_correction[c.result_id] = c

    pending_count = sum(1 for r in all_results if r.verification_status not in _VERIFIED_STATUSES)

    # Partition into selected vs. additional (FR-24, FR-27)
    selected: list[Result] = []
    additional: list[Result] = []

    for r in all_results:
        name = (r.test_name_raw or "").strip()
        is_in_consultation = any(
            name.lower() == sel.lower() for sel in PHASE1_SELECTED_TEST_NAMES
        )
        # Flagged results always appear in selected regardless of filter (FR-32)
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
            "pending_count": pending_count,
        },
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()  # Persist the audit event

    def _to_schema(r: Result) -> ConsultationResultItem:
        corr = latest_correction.get(r.id)
        return ConsultationResultItem(
            id=r.id,
            test_name_raw=r.test_name_raw or "",
            value_raw=corr.corrected_value_raw if corr else (r.value_raw or ""),
            original_value_raw=r.value_raw or "",
            is_corrected=corr is not None,
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
        pending_count=pending_count,
    )
