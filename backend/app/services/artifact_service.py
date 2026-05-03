from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models.artifact import Artifact
from app.domain.enums import ArtifactStatus, RunStatus
from app.infrastructure.storage import StorageBackend, get_storage_backend
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactComplete, ArtifactCreate
from app.services.quota_service import QuotaService


class ArtifactService:
    def __init__(self, db: Session, storage: StorageBackend | None = None) -> None:
        self.db = db
        self.runs = RunRepository(db)
        self.artifacts = ArtifactRepository(db)
        self.quotas = QuotaService(db)
        self.storage = storage or get_storage_backend()

    def create_artifact(self, run_id: UUID, data: ArtifactCreate) -> Artifact:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Completed run cannot accept artifacts")

        self.quotas.ensure_can_create_artifact(
            workspace_id=run.workspace_id,
            size_bytes=data.size_bytes,
        )

        artifact = self.artifacts.create(
            workspace_id=run.workspace_id,
            run_id=run.id,
            name=data.name,
            kind=data.kind,
            size_bytes=data.size_bytes,
            content_type=data.content_type,
            hash_=data.hash,
            meta=data.meta,
        )

        artifact.storage_uri = self.storage.build_artifact_uri(
            workspace_id=run.workspace_id,
            run_id=run.id,
            artifact_id=artifact.id,
            name=artifact.name,
        )

        self.quotas.refresh_workspace_quota(run.workspace_id)

        self.db.commit()
        self.db.refresh(artifact)

        return artifact

    def list_run_artifacts(self, run_id: UUID) -> list[Artifact]:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        return self.artifacts.list_by_run_id(run_id)

    def get_artifact(self, artifact_id: UUID) -> Artifact:
        artifact = self.artifacts.get(artifact_id)
        if artifact is None:
            raise LookupError("Artifact not found")

        return artifact

    def complete_artifact(self, artifact_id: UUID, data: ArtifactComplete) -> Artifact:
        artifact = self.get_artifact(artifact_id)

        if artifact.status == ArtifactStatus.DELETED.value:
            raise ValueError("Deleted artifact cannot be completed")

        old_size_bytes = artifact.size_bytes or 0
        new_size_bytes = data.size_bytes if data.size_bytes is not None else old_size_bytes
        size_delta = new_size_bytes - old_size_bytes

        self.quotas.ensure_can_add_storage_delta(
            workspace_id=artifact.workspace_id,
            delta_bytes=size_delta,
        )

        storage_uri = data.storage_uri or artifact.storage_uri
        if storage_uri is None:
            storage_uri = self.storage.build_artifact_uri(
                workspace_id=artifact.workspace_id,
                run_id=artifact.run_id,
                artifact_id=artifact.id,
                name=artifact.name,
            )

        artifact = self.artifacts.complete(
            artifact=artifact,
            storage_uri=storage_uri,
            size_bytes=data.size_bytes,
            content_type=data.content_type,
            hash_=data.hash,
            meta=data.meta,
        )

        self.quotas.refresh_workspace_quota(artifact.workspace_id)

        self.db.commit()
        self.db.refresh(artifact)

        return artifact

    def upload_artifact_file(self, artifact_id: UUID, file: UploadFile) -> Artifact:
        artifact = self.get_artifact(artifact_id)

        if artifact.status == ArtifactStatus.DELETED.value:
            raise ValueError("Deleted artifact cannot be uploaded")

        if artifact.status == ArtifactStatus.UPLOADED.value:
            raise ValueError("Uploaded artifact cannot be uploaded again")

        old_size_bytes = artifact.size_bytes or 0
        upload_size_bytes = self._get_upload_size_bytes(file)

        if upload_size_bytes is not None:
            self.quotas.ensure_can_add_storage_delta(
                workspace_id=artifact.workspace_id,
                delta_bytes=upload_size_bytes - old_size_bytes,
            )

        stored = self.storage.save_artifact_file(
            workspace_id=artifact.workspace_id,
            run_id=artifact.run_id,
            artifact_id=artifact.id,
            name=artifact.name,
            fileobj=file.file,
            content_type=file.content_type,
        )

        self.quotas.ensure_can_add_storage_delta(
            workspace_id=artifact.workspace_id,
            delta_bytes=stored.size_bytes - old_size_bytes,
        )

        meta = {
            **(artifact.meta or {}),
            "storage_mode": "local_upload",
            "uploaded_filename": file.filename,
        }

        artifact = self.artifacts.complete(
            artifact=artifact,
            storage_uri=stored.storage_uri,
            size_bytes=stored.size_bytes,
            content_type=stored.content_type,
            hash_=stored.sha256,
            meta=meta,
        )

        self.quotas.refresh_workspace_quota(artifact.workspace_id)

        self.db.commit()
        self.db.refresh(artifact)

        return artifact

    def get_download_reference(self, artifact_id: UUID) -> tuple[Artifact, str]:
        artifact = self.get_artifact(artifact_id)

        if artifact.status != ArtifactStatus.UPLOADED.value:
            raise ValueError("Artifact is not uploaded")

        if artifact.storage_uri is None:
            raise ValueError("Artifact has no storage URI")

        download_url = self.storage.get_download_url(
            artifact_id=artifact.id,
            storage_uri=artifact.storage_uri,
        )

        return artifact, download_url

    def get_content_path(self, artifact_id: UUID) -> tuple[Artifact, str]:
        artifact = self.get_artifact(artifact_id)

        if artifact.status != ArtifactStatus.UPLOADED.value:
            raise ValueError("Artifact is not uploaded")

        if artifact.storage_uri is None:
            raise ValueError("Artifact has no storage URI")

        path = self.storage.get_artifact_path(artifact.storage_uri)

        return artifact, str(path)

    @staticmethod
    def _get_upload_size_bytes(file: UploadFile) -> int | None:
        try:
            current_position = file.file.tell()
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
            file.file.seek(current_position)
        except (OSError, ValueError):
            return None

        return size_bytes
