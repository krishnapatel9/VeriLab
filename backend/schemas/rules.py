from pydantic import BaseModel, ConfigDict, Field, UUID4
from typing import List, Optional
from datetime import datetime


class RuleItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    name: str
    description: Optional[str] = None
    version: int
    status: str
    approved_test_names: List[str]
    suggested_test_names: List[str] = []
    created_at: datetime
    updated_at: datetime


class RuleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    approved_test_names: List[str] = Field(min_length=1)
    suggested_test_names: List[str] = []


class RulePublishRequest(BaseModel):
    approved_test_names: List[str] = Field(min_length=1)
    suggested_test_names: List[str] = []
