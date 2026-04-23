from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from urllib.parse import quote
from uuid import UUID


@dataclass(frozen=True)
class StoredArtifact:
    storage_uri: str
    path: Path
    size_bytes: int
    sha256: str
    content_type: str | None


class StorageBackend:
    def build_artifact_uri(
            self,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
    ) -> str:
        raise NotImplementedError

    def save_artifact_file(
            self,
            *,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
            fileobj: BinaryIO,
            content_type: str | None,
    ) -> StoredArtifact:
        raise NotImplementedError

    def get_artifact_path(self, storage_uri: str) -> Path:
        raise NotImplementedError

    def get_download_url(self, artifact_id: UUID, storage_uri: str) -> str:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self, root_dir: str | Path = ".saltai-cloud/artifacts") -> None:
        self.root_dir = Path(root_dir).expanduser().resolve()

    def build_artifact_uri(
            self,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
    ) -> str:
        return f"file://{self._artifact_path(workspace_id, run_id, artifact_id, name)}"

    def save_artifact_file(
            self,
            *,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
            fileobj: BinaryIO,
            content_type: str | None,
    ) -> StoredArtifact:
        path = self._artifact_path(workspace_id, run_id, artifact_id, name)
        path.parent.mkdir(parents=True, exist_ok=True)

        sha256 = hashlib.sha256()
        size_bytes = 0

        with path.open("wb") as out:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break

                size_bytes += len(chunk)
                sha256.update(chunk)
                out.write(chunk)

        return StoredArtifact(
            storage_uri=f"file://{path}",
            path=path,
            size_bytes=size_bytes,
            sha256=sha256.hexdigest(),
            content_type=content_type,
        )

    def get_artifact_path(self, storage_uri: str) -> Path:
        if not storage_uri.startswith("file://"):
            raise ValueError("Only file:// artifacts are supported by local storage")

        path = Path(storage_uri[7:]).expanduser().resolve()

        try:
            path.relative_to(self.root_dir)
        except ValueError as exc:
            raise ValueError("Artifact path is outside local storage root") from exc

        if not path.exists():
            raise LookupError("Artifact file not found in local storage")

        if not path.is_file():
            raise ValueError("Artifact storage path is not a file")

        return path

    def get_download_url(self, artifact_id: UUID, storage_uri: str) -> str:
        return storage_uri

    def _artifact_path(
            self,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
    ) -> Path:
        safe_name = quote(name, safe="")
        return (
                self.root_dir
                / "workspaces"
                / str(workspace_id)
                / "runs"
                / str(run_id)
                / "artifacts"
                / str(artifact_id)
                / safe_name
        )


def get_storage_backend() -> StorageBackend:
    return LocalStorageBackend()
