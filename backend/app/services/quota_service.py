from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.quota import Quota
from app.db.models.workspace import Workspace
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.quota_repository import QuotaRepository
from app.repositories.run_repository import RunRepository
from app.repositories.workspace_repository import WorkspaceRepository


class QuotaExceededError(ValueError):
    pass


class QuotaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.quotas = QuotaRepository(db)
        self.projects = ProjectRepository(db)
        self.runs = RunRepository(db)
        self.artifacts = ArtifactRepository(db)

    def ensure_can_create_project(self, workspace_id: UUID) -> None:
        workspace = self._get_workspace(workspace_id)

        if workspace.plan is None or workspace.plan.max_projects is None:
            return

        used_projects = self.projects.count_by_workspace_id(workspace_id)
        self._ensure_limit(
            name="projects",
            requested=used_projects + 1,
            limit=workspace.plan.max_projects,
        )

    def ensure_can_create_run(self, workspace_id: UUID) -> None:
        workspace = self._get_workspace(workspace_id)

        if workspace.plan is None or workspace.plan.max_runs is None:
            return

        used_runs = self.runs.count_by_workspace_id(workspace_id)
        self._ensure_limit(
            name="runs",
            requested=used_runs + 1,
            limit=workspace.plan.max_runs,
        )

    def ensure_can_create_artifact(
            self,
            workspace_id: UUID,
            size_bytes: int | None = None,
    ) -> None:
        workspace = self._get_workspace(workspace_id)

        if workspace.plan is None:
            return

        if workspace.plan.max_artifacts is not None:
            used_artifacts = self.artifacts.count_by_workspace_id(workspace_id)
            self._ensure_limit(
                name="artifacts",
                requested=used_artifacts + 1,
                limit=workspace.plan.max_artifacts,
            )

        if size_bytes is not None:
            self.ensure_can_add_storage_delta(
                workspace_id=workspace_id,
                delta_bytes=size_bytes,
            )

    def ensure_can_add_storage_delta(
            self,
            workspace_id: UUID,
            delta_bytes: int,
    ) -> None:
        if delta_bytes <= 0:
            return

        workspace = self._get_workspace(workspace_id)

        if workspace.plan is None or workspace.plan.max_storage_bytes is None:
            return

        used_storage_bytes = self.artifacts.sum_size_by_workspace_id(workspace_id)
        self._ensure_limit(
            name="storage bytes",
            requested=used_storage_bytes + delta_bytes,
            limit=workspace.plan.max_storage_bytes,
        )

    def refresh_workspace_quota(self, workspace_id: UUID) -> Quota:
        self._get_workspace(workspace_id)

        quota = self.quotas.get_or_create_by_workspace_id(workspace_id)

        return self.quotas.update_usage(
            quota=quota,
            used_projects=self.projects.count_by_workspace_id(workspace_id),
            used_runs=self.runs.count_by_workspace_id(workspace_id),
            used_artifacts=self.artifacts.count_by_workspace_id(workspace_id),
            used_storage_bytes=self.artifacts.sum_size_by_workspace_id(workspace_id),
        )

    def _get_workspace(self, workspace_id: UUID) -> Workspace:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        return workspace

    @staticmethod
    def _ensure_limit(name: str, requested: int, limit: int) -> None:
        if requested > limit:
            raise QuotaExceededError(
                f"Quota exceeded: {name} limit is {limit}"
            )
