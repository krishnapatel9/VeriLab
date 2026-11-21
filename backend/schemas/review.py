from pydantic import BaseModel, ConfigDict, Field, UUID4
from typing import List, Optional
from datetime import datetime


class ResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    test_name_raw: Optional[str] = None
    value_raw: Optional[str] = None
    unit_raw: Optional[str] = None
    reference_range_raw: Optional[str] = None
    flag_raw: Optional[str] = None
    confidence_value: Optional[float] = None
    source_page: Optional[int] = None
    source_x: Optional[float] = None
    source_y: Optional[float] = None
    source_width: Optional[float] = None
    source_height: Optional[float] = None
    verification_status: str
    is_critical: bool = False


class ReviewItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    result_id: Optional[UUID4] = None
    item_type: str
    flag_reason: str
    status: str


class ReportReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    file_hash: str
    status: str
    created_at: datetime
    results: List[ResultItem]
    review_items: List[ReviewItemSchema] = []


class VerifyResultRequest(BaseModel):
    reviewer_user_id: Optional[UUID4] = None


class CorrectResultRequest(BaseModel):
    reviewer_user_id: Optional[UUID4] = None
    corrected_value_raw: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=200)
    comment: Optional[str] = None
