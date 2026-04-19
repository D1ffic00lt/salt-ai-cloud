from urllib.parse import quote
from uuid import UUID


class StorageBackend:
    def build_artifact_uri(
            self,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
    ) -> str:
        raise NotImplementedError

    def get_download_url(self, artifact_id: UUID, storage_uri: str) -> str:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def build_artifact_uri(
            self,
            workspace_id: UUID,
            run_id: UUID,
            artifact_id: UUID,
            name: str,
    ) -> str:
        safe_name = quote(name, safe="")
        return (
            f"local://workspaces/{workspace_id}/runs/{run_id}/"
            f"artifacts/{artifact_id}/{safe_name}"
        )

    def get_download_url(self, artifact_id: UUID, storage_uri: str) -> str:
        return storage_uri


def get_storage_backend() -> StorageBackend:
    return LocalStorageBackend()
