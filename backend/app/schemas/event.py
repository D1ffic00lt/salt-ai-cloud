from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EventLevel


class EventCreate(BaseModel):
    type: str = Field(min_length=1, max_length=128)
    level: str = Field(default=EventLevel.INFO.value, max_length=32)
    message: str | None = None
    payload: dict = Field(default_factory=dict)
    timestamp: datetime | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    run_id: UUID
    type: str
    level: str
    message: str | None
    payload: dict
    timestamp: datetime
    created_at: datetime
