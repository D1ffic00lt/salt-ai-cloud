from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    user_id: UUID
    scopes: list[str] = Field(default_factory=lambda: ["runs:write", "artifacts:write"])
    expires_at: datetime | None = None


class ApiTokenCreated(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    name: str
    token: str
    token_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


class ApiTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    name: str
    token_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class CurrentApiUser(BaseModel):
    user_id: UUID
    workspace_id: UUID
    token_id: UUID
    scopes: list[str]
