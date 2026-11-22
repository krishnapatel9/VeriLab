import hashlib
import uuid
import os
from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models.core_models import Report, generate_uuidv7
from constants import MAX_UPLOAD_BYTES
from services.storage import get_storage

class IntakeService:
    @staticmethod
    async def process_upload(
        file: UploadFile, 
        db: Session, 
        tenant_id: uuid.UUID, 
        uploader_id: uuid.UUID
    ) -> Report:
        """
        Processes an uploaded lab report:
        1. Reads and hashes the file (SHA-256)
        2. Saves to 'object storage' (local mock)
        3. Creates a Database record with status 'intake_pending'
        """
        
        # 1. Read and Hash
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty (0 bytes)",
            )
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {MAX_UPLOAD_BYTES} byte upload limit",
            )

        # Tier 1.6 File Validation Checks
        if contents.startswith(b"MZ") or b"<script" in contents[:512].lower():
            raise HTTPException(
                status_code=400,
                detail="Potentially harmful executable or script content detected in file upload",
            )

        suffix = os.path.splitext(file.filename or "")[1].lower()
        if suffix == ".pdf":
            # Check for encrypted PDF markers
            if b"/Encrypt" in contents[:4096] or b"/Encrypt" in contents[-2048:]:
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted or password-protected PDFs are not accepted",
                )

        file_hash = hashlib.sha256(contents).hexdigest()
        
        # 2. Save to tenant-scoped storage (local disk or R2, see services/storage.py)
        suffix = os.path.splitext(file.filename or "")[1].lower()
        storage_filename = f"{file_hash}{suffix}"
        file_object_key = f"{tenant_id}/{storage_filename}"
        get_storage().put(file_object_key, contents, db)

        # Reset file pointer if needed by other services
        await file.seek(0)

        # 3. Create DB Record
        new_report = Report(
            id=generate_uuidv7(),
            tenant_id=tenant_id,
            uploader_user_id=uploader_id,
            file_object_key=file_object_key,
            file_hash=file_hash,
            status="intake_pending",
            report_status_extracted="unknown",
            match_status="unmatched",
            page_count=1 # Mock page count for now
        )
        
        db.add(new_report)
        db.flush()  # caller commits together with the audit event
        
        return new_report
