from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import List

class ReportListItem(BaseModel):
    id: uuid.UUID
    file_hash: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReportListResponse(BaseModel):
    reports: List[ReportListItem]

class UploadResponse(BaseModel):
    report_id: uuid.UUID
    file_hash: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)
