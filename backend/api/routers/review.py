from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from api.dependencies import get_db, require_role
from db.models.core_models import Report, Result, ResultCorrection, ReviewItem, User
from schemas.review import ReportReviewResponse, VerifyResultRequest, CorrectResultRequest
from core.audit import emit_audit_event

router = APIRouter(prefix="/api/v1/review", tags=["Review"])


@router.get("/reports/{report_id}", response_model=ReportReviewResponse)
def get_report_for_review(
    report_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "admin"]))
):
    """
    Fetches a specific report along with all its extracted OCR results and
    open ReviewItems. Used by the Clinical Review UI to populate the side-by-side view.
    """
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.tenant_id == current_user.tenant_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    results = (
        db.query(Result)
        .filter(Result.report_id == report_id, Result.tenant_id == current_user.tenant_id)
        .all()
    )
    review_items = (
        db.query(ReviewItem)
        .filter(
            ReviewItem.report_id == report_id,
            ReviewItem.tenant_id == current_user.tenant_id,
            ReviewItem.status == "open",
        )
        .all()
    )

    # Audit: reviewer opened the report
    emit_audit_event(
        db=db,
        event_type="report.review_opened",
        resource_type="report",
        resource_id=report_id,
        metadata={"result_count": len(results), "open_review_items": len(review_items)},
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()  # Commit the audit event (GET requests don't commit otherwise)

    return {
        "id": report.id,
        "file_hash": report.file_hash,
        "status": report.status,
        "created_at": report.created_at,
        "results": results,
        "review_items": review_items,
    }


@router.post("/results/{result_id}/verify")
def verify_result(
    result_id: uuid.UUID,
    request: VerifyResultRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "admin"]))
):
    result = (
        db.query(Result)
        .filter(Result.id == result_id, Result.tenant_id == current_user.tenant_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    prev_status = result.verification_status
    result.verification_status = "verified_as_reported"

    # Close any open ReviewItem linked to this result (Task 1.3)
    open_items = (
        db.query(ReviewItem)
        .filter(
            ReviewItem.result_id == result_id,
            ReviewItem.tenant_id == current_user.tenant_id,
            ReviewItem.status == "open",
        )
        .all()
    )
    now = datetime.now(timezone.utc)
    for item in open_items:
        item.status = "resolved"
        item.resolved_at = now

    db.commit()

    # Audit
    emit_audit_event(
        db=db,
        event_type="result.verified",
        resource_type="result",
        resource_id=result_id,
        metadata={
            "reviewer_user_id": str(current_user.id),
            "prev_status": prev_status,
            "new_status": "verified_as_reported",
            "review_items_closed": len(open_items),
        },
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()  # Persist the audit event

    return {"status": "success", "verification_status": result.verification_status}


@router.post("/results/{result_id}/correct")
def correct_result(
    result_id: uuid.UUID,
    request: CorrectResultRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "admin"]))
):
    result = (
        db.query(Result)
        .filter(Result.id == result_id, Result.tenant_id == current_user.tenant_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    prev_value = result.value_raw
    prev_status = result.verification_status

    # Safety Invariant: Additive Correction — original is never mutated
    correction = ResultCorrection(
        result_id=result.id,
        original_value_raw=result.value_raw,
        corrected_value_raw=request.corrected_value_raw,
        reviewer_user_id=current_user.id,
        reason=request.reason,
        comment=request.comment,
    )
    db.add(correction)

    # State machine transition
    result.verification_status = "verified_with_correction"

    # Close any open ReviewItem linked to this result
    open_items = (
        db.query(ReviewItem)
        .filter(
            ReviewItem.result_id == result_id,
            ReviewItem.tenant_id == current_user.tenant_id,
            ReviewItem.status == "open",
        )
        .all()
    )
    now = datetime.now(timezone.utc)
    for item in open_items:
        item.status = "resolved"
        item.resolved_at = now

    db.commit()

    # Audit
    emit_audit_event(
        db=db,
        event_type="result.corrected",
        resource_type="result",
        resource_id=result_id,
        metadata={
            "reviewer_user_id": str(current_user.id),
            "prev_value": prev_value,
            "corrected_value": request.corrected_value_raw,
            "reason": request.reason,
            "prev_status": prev_status,
            "new_status": "verified_with_correction",
            "review_items_closed": len(open_items),
        },
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()  # Persist the audit event

    return {"status": "success", "verification_status": result.verification_status}

