import hashlib
import uuid
import os
from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models.core_models import Report, generate_uuidv7
from constants import MAX_UPLOAD_BYTES

# Mock object storage path for local development
STORAGE_DIR = "mock_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

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
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {MAX_UPLOAD_BYTES} byte upload limit",
            )
        file_hash = hashlib.sha256(contents).hexdigest()
        
        # 2. Save to tenant-scoped object storage (Mock)
        suffix = os.path.splitext(file.filename or "")[1].lower()
        storage_filename = f"{file_hash}{suffix}"
        file_object_key = f"{tenant_id}/{storage_filename}"
        tenant_storage_dir = os.path.join(STORAGE_DIR, str(tenant_id))
        os.makedirs(tenant_storage_dir, exist_ok=True)
        local_path = os.path.join(tenant_storage_dir, storage_filename)
        
        with open(local_path, "wb") as f:
            f.write(contents)
            
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
