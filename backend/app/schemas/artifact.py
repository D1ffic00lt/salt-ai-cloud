from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ArtifactKind, ArtifactStatus


class ArtifactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(default=ArtifactKind.OTHER.value, max_length=64)
    size_bytes: int | None = Field(default=None, ge=0)
    content_type: str | None = Field(default=None, max_length=255)
    hash: str | None = Field(default=None, max_length=128)
    meta: dict = Field(default_factory=dict)


class ArtifactComplete(BaseModel):
    storage_uri: str | None = Field(default=None, max_length=2048)
    size_bytes: int | None = Field(default=None, ge=0)
    content_type: str | None = Field(default=None, max_length=255)
    hash: str | None = Field(default=None, max_length=128)
    meta: dict | None = None


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    run_id: UUID
    name: str
    kind: str
    storage_uri: str | None
    size_bytes: int | None
    content_type: str | None
    hash: str | None
    status: str
    meta: dict
    created_at: datetime
    completed_at: datetime | None


class ArtifactDownloadRead(BaseModel):
    artifact_id: UUID
    storage_uri: str
    download_url: str
