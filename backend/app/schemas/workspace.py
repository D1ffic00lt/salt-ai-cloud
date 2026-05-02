from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.project import ProjectRead


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=128)
    owner_user_id: UUID | None = None
    plan_id: UUID | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    plan_id: UUID | None
    created_at: datetime
    updated_at: datetime


class WorkspaceDetailsRead(BaseModel):
    workspace: WorkspaceRead
    projects: list[ProjectRead] = Field(default_factory=list)
