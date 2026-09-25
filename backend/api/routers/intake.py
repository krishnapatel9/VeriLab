from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import asyncio

from api.dependencies import get_db, SessionLocal
from services.intake_service import IntakeService
from schemas.intake import UploadResponse, ReportListResponse
from db.models.core_models import User, Report
from services.ocr_service import OCRService
from core.audit import emit_audit_event
from core.audit import emit_audit_event
from api.dependencies import require_role
from constants import ALLOWED_UPLOAD_SUFFIXES

router = APIRouter(prefix="/api/v1/intake", tags=["Intake"])


def trigger_ocr_background(report_id: uuid.UUID, tenant_id: uuid.UUID):
    """Background task: open a fresh DB session and run OCR + audit."""
    db = SessionLocal()
    try:
        ocr_service = OCRService(db_session=db)
        asyncio.run(ocr_service.process_report(report_id))
        # Audit: OCR completed
        emit_audit_event(
            db=db,
            event_type="report.ocr_completed",
            resource_type="report",
            resource_id=report_id,
            metadata={"ocr_provider": "MockOCRProvider"},
            actor_user_id=None,  # system event
            tenant_id=tenant_id,
        )
    except Exception as e:
        print(f"Background OCR failed for {report_id}: {e}")
    finally:
        db.close()


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["uploader", "reviewer", "admin", "doctor"]))
):
    """
    List reports for the current user's tenant.
    """
    reports = db.query(Report).filter(Report.tenant_id == current_user.tenant_id).order_by(Report.created_at.desc()).all()
    return ReportListResponse(reports=reports)

@router.post("/upload", response_model=UploadResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["uploader", "admin"]))
):
    """
    Upload a lab report PDF/Image.

    Upload a lab report PDF/Image.

    Triggers OCR asynchronously via a background task.
    """
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{suffix}'. Accepted: {', '.join(ALLOWED_UPLOAD_SUFFIXES)}"
        )

    try:
        report = await IntakeService.process_upload(
            file=file,
            db=db,
            tenant_id=current_user.tenant_id,
            uploader_id=current_user.id,
        )

        # Audit: report uploaded
        emit_audit_event(
            db=db,
            event_type="report.uploaded",
            resource_type="report",
            resource_id=report.id,
            metadata={
                "filename": file.filename,
                "file_hash": report.file_hash,
                "tenant_id": str(current_user.tenant_id),
            },
            actor_user_id=current_user.id,
            tenant_id=current_user.tenant_id,
        )
        db.commit()  # Persist the audit event before background task starts

        # Trigger OCR asynchronously
        background_tasks.add_task(trigger_ocr_background, report.id, current_user.tenant_id)

        return UploadResponse(
            report_id=report.id,
            file_hash=report.file_hash,
            status=report.status,
            message="File uploaded and hashed successfully. OCR processing started.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

