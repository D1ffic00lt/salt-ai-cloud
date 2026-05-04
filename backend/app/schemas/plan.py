from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    max_projects: int | None = Field(default=None, ge=0)
    max_runs: int | None = Field(default=None, ge=0)
    max_artifacts: int | None = Field(default=None, ge=0)
    max_storage_bytes: int | None = Field(default=None, ge=0)


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    max_projects: int | None
    max_runs: int | None
    max_artifacts: int | None
    max_storage_bytes: int | None
    created_at: datetime


class WorkspacePlanUpdate(BaseModel):
    plan_id: UUID | None = None
