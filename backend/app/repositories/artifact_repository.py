from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.artifact import Artifact
from app.db.models.run import Run
from app.domain.enums import ArtifactStatus


class ArtifactRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, artifact_id: UUID) -> Artifact | None:
        statement = select(Artifact).where(Artifact.id == artifact_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list_by_run_id(self, run_id: UUID) -> list[Artifact]:
        statement = (
            select(Artifact)
            .where(Artifact.run_id == run_id)
            .order_by(Artifact.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def count_by_workspace_id(self, workspace_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Artifact)
            .where(Artifact.workspace_id == workspace_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def count_by_project_id(self, project_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Artifact)
            .join(Run, Artifact.run_id == Run.id)
            .where(Run.project_id == project_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def sum_size_by_workspace_id(self, workspace_id: UUID) -> int:
        statement = (
            select(func.coalesce(func.sum(Artifact.size_bytes), 0))
            .select_from(Artifact)
            .where(Artifact.workspace_id == workspace_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def sum_size_by_project_id(self, project_id: UUID) -> int:
        statement = (
            select(func.coalesce(func.sum(Artifact.size_bytes), 0))
            .select_from(Artifact)
            .join(Run, Artifact.run_id == Run.id)
            .where(Run.project_id == project_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def create(
            self,
            workspace_id: UUID,
            run_id: UUID,
            name: str,
            kind: str,
            size_bytes: int | None = None,
            content_type: str | None = None,
            hash_: str | None = None,
            meta: dict | None = None,
    ) -> Artifact:
        artifact = Artifact(
            workspace_id=workspace_id,
            run_id=run_id,
            name=name,
            kind=kind,
            size_bytes=size_bytes,
            content_type=content_type,
            hash=hash_,
            status=ArtifactStatus.PENDING.value,
            meta=meta or {},
        )

        self.db.add(artifact)
        self.db.flush()
        return artifact

    def complete(
            self,
            artifact: Artifact,
            storage_uri: str | None = None,
            size_bytes: int | None = None,
            content_type: str | None = None,
            hash_: str | None = None,
            meta: dict | None = None,
    ) -> Artifact:
        if storage_uri is not None:
            artifact.storage_uri = storage_uri

        if size_bytes is not None:
            artifact.size_bytes = size_bytes

        if content_type is not None:
            artifact.content_type = content_type

        if hash_ is not None:
            artifact.hash = hash_

        if meta is not None:
            artifact.meta = meta

        artifact.status = ArtifactStatus.UPLOADED.value
        artifact.completed_at = datetime.now(timezone.utc)

        self.db.flush()
        return artifact
