from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MetricCreate(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int | None = None
    payload: dict = Field(default_factory=dict)
    timestamp: datetime | None = None


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    run_id: UUID
    key: str
    value: float
    step: int | None
    payload: dict
    timestamp: datetime
    created_at: datetime
