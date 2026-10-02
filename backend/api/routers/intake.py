from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
import uuid
import asyncio
import logging

from api.dependencies import get_db, SessionLocal
from services.intake_service import IntakeService
from schemas.intake import UploadResponse, ReportListResponse
from db.models.core_models import User, Report
from services.ocr_service import OCRService
from core.audit import emit_audit_event
from api.dependencies import require_role
from constants import ALLOWED_UPLOAD_SUFFIXES

router = APIRouter(prefix="/api/v1/intake", tags=["Intake"])
logger = logging.getLogger(__name__)

# Magic bytes per accepted suffix: the extension alone is attacker-controlled.
_MAGIC = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


def trigger_ocr_background(report_id: uuid.UUID, tenant_id: uuid.UUID):
    """Background task: open a fresh DB session and run OCR + audit."""
    db = SessionLocal()
    try:
        ocr_service = OCRService(db_session=db)
        asyncio.run(ocr_service.process_report(report_id))
        report = db.query(Report).filter(Report.id == report_id).first()
        # Audit: success and failure are both recorded, and actually committed.
        emit_audit_event(
            db=db,
            event_type="report.ocr_completed" if report and report.status == "processed" else "report.ocr_failed",
            resource_type="report",
            resource_id=report_id,
            metadata={"ocr_provider": type(ocr_service.provider).__name__,
                      "report_status": report.status if report else "missing"},
            actor_user_id=None,  # system event
            tenant_id=tenant_id,
        )
        db.commit()
    except Exception:
        logger.exception("Background OCR failed for report %s", report_id)
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

_MEDIA = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@router.get("/reports/{report_id}/file")
def get_original_file(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "doctor", "admin"])),
):
    """Serve the immutable original (FR-29). Tenant-scoped; every view is audited."""
    report = db.query(Report).filter(
        Report.id == report_id, Report.tenant_id == current_user.tenant_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    path = os.path.join("mock_storage", report.file_object_key)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Original file is missing from storage")
    emit_audit_event(
        db=db, event_type="report.file_viewed", resource_type="report", resource_id=report.id,
        metadata={"file_hash": report.file_hash},
        actor_user_id=current_user.id, tenant_id=current_user.tenant_id,
    )
    db.commit()
    media = _MEDIA.get(os.path.splitext(path)[1].lower(), "application/octet-stream")
    return FileResponse(path, media_type=media, headers={"Cache-Control": "private, no-store"})


@router.post("/upload", response_model=UploadResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["uploader", "admin"]))
):
    """
    Upload a lab report PDF/Image.

    Triggers OCR asynchronously via a background task.
    """
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{suffix}'. Accepted: {', '.join(ALLOWED_UPLOAD_SUFFIXES)}"
        )

    head = await file.read(16)
    await file.seek(0)
    if not any(head.startswith(m) for m in _MAGIC[suffix]):
        raise HTTPException(status_code=400, detail="File content does not match its extension")

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
    except Exception:
        db.rollback()
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Upload failed")

