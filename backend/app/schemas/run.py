from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    config: dict = Field(default_factory=dict)
    manifest: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_by_id: UUID | None = None


class RunUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    config: dict | None = None
    manifest: dict | None = None
    tags: list[str] | None = None


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    project_id: UUID
    created_by_id: UUID | None
    name: str | None
    status: str
    config: dict
    manifest: dict
    tags: list
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
