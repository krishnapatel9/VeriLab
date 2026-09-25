from pydantic import BaseModel
from typing import List
import uuid


class ConsultationResultItem(BaseModel):
    """A single lab result as presented in the doctor's consultation view."""
    id: uuid.UUID
    test_name_raw: str
    value_raw: str
    unit_raw: str | None
    reference_range_raw: str | None
    flag_raw: str | None
    is_critical: bool
    verification_status: str
    # Source coordinates for "jump to original" linking
    source_page: int
    source_x: float
    source_y: float
    source_width: float
    source_height: float

    class Config:
        from_attributes = True


class ConsultationResponse(BaseModel):
    """
    The full response for the doctor consultation view.

    selected_results   — tests that match the active consultation type rule set.
    additional_results — all other extracted results; disclosed per FR-24/FR-27.
    rule_version       — the rules config version used for filtering.
    """
    report_id: uuid.UUID
    report_status: str
    rule_version: int
    consultation_type: str
    selected_results: List[ConsultationResultItem]
    additional_results: List[ConsultationResultItem]

    class Config:
        from_attributes = True
