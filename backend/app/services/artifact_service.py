from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models.artifact import Artifact
from app.domain.enums import ArtifactStatus, RunStatus
from app.infrastructure.storage import StorageBackend, get_storage_backend
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactComplete, ArtifactCreate


class ArtifactService:
    def __init__(self, db: Session, storage: StorageBackend | None = None) -> None:
        self.db = db
        self.runs = RunRepository(db)
        self.artifacts = ArtifactRepository(db)
        self.storage = storage or get_storage_backend()

    def create_artifact(self, run_id: UUID, data: ArtifactCreate) -> Artifact:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Completed run cannot accept artifacts")

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

        self.db.commit()
        self.db.refresh(artifact)

        return artifact

    def upload_artifact_file(self, artifact_id: UUID, file: UploadFile) -> Artifact:
        artifact = self.get_artifact(artifact_id)

        if artifact.status == ArtifactStatus.DELETED.value:
            raise ValueError("Deleted artifact cannot be uploaded")

        if artifact.status == ArtifactStatus.UPLOADED.value:
            raise ValueError("Uploaded artifact cannot be uploaded again")

        stored = self.storage.save_artifact_file(
            workspace_id=artifact.workspace_id,
            run_id=artifact.run_id,
            artifact_id=artifact.id,
            name=artifact.name,
            fileobj=file.file,
            content_type=file.content_type,
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
