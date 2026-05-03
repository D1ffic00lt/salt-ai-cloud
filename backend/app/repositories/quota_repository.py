from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.quota import Quota


class QuotaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_workspace_id(self, workspace_id: UUID) -> Quota | None:
        statement = select(Quota).where(Quota.workspace_id == workspace_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_or_create_by_workspace_id(self, workspace_id: UUID) -> Quota:
        quota = self.get_by_workspace_id(workspace_id)
        if quota is not None:
            return quota

        quota = Quota(workspace_id=workspace_id)
        self.db.add(quota)
        self.db.flush()

        return quota

    def update_usage(
            self,
            quota: Quota,
            used_projects: int,
            used_runs: int,
            used_artifacts: int,
            used_storage_bytes: int,
    ) -> Quota:
        quota.used_projects = used_projects
        quota.used_runs = used_runs
        quota.used_artifacts = used_artifacts
        quota.used_storage_bytes = used_storage_bytes

        self.db.flush()

        return quota
