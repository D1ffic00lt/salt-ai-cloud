from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.workspace import WorkspaceRead

DEFAULT_API_TOKEN_SCOPES = [
    "workspaces:read",
    "workspaces:write",
    "projects:read",
    "projects:write",
    "runs:read",
    "runs:write",
    "metrics:read",
    "metrics:write",
    "events:read",
    "events:write",
    "artifacts:read",
    "artifacts:write",
    "tokens:write",
]


class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    user_id: UUID
    scopes: list[str] = Field(default_factory=DEFAULT_API_TOKEN_SCOPES.copy)
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


class BootstrapCreate(BaseModel):
    workspace_name: str = Field(min_length=1, max_length=255)
    workspace_slug: str = Field(min_length=1, max_length=128)
    plan_id: UUID | None = None

    telegram_id: int | None = None
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)

    token_name: str = Field(default="owner", min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: ["*"])
    expires_at: datetime | None = None


class BootstrapUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telegram_id: int | None
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime
    updated_at: datetime


class BootstrapCreated(BaseModel):
    user: BootstrapUserRead
    workspace: WorkspaceRead
    api_token: ApiTokenCreated
