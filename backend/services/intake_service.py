import hashlib
import uuid
import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
from db.models.core_models import Report, generate_uuidv7

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
        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()
        
        # 2. Save to Immutable Object Storage (Mock)
        file_object_key = f"{tenant_id}/{file_hash}_{file.filename}"
        local_path = os.path.join(STORAGE_DIR, f"{file_hash}_{file.filename}")
        
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
        db.commit()
        db.refresh(new_report)
        
        return new_report
