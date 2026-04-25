from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.enums import RunStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.event_repository import EventRepository
from app.repositories.metric_repository import MetricRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.overview import (
    ProjectOverviewCounters,
    ProjectOverviewRead,
    RunStatusCounters,
    WorkspaceOverviewCounters,
    WorkspaceOverviewRead,
)
from app.schemas.project import ProjectRead
from app.schemas.run import RunRead
from app.schemas.workspace import WorkspaceRead


class OverviewService:
    def __init__(self, db: Session) -> None:
        self.workspaces = WorkspaceRepository(db)
        self.projects = ProjectRepository(db)
        self.runs = RunRepository(db)
        self.metrics = MetricRepository(db)
        self.events = EventRepository(db)
        self.artifacts = ArtifactRepository(db)

    def get_workspace_overview(
            self,
            workspace_id: UUID,
            recent_runs_limit: int,
    ) -> WorkspaceOverviewRead:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        projects = self.projects.list_by_workspace_id(workspace_id)
        recent_runs = self.runs.list_recent_by_workspace_id(
            workspace_id=workspace_id,
            limit=recent_runs_limit,
        )

        counters = WorkspaceOverviewCounters(
            projects_count=self.projects.count_by_workspace_id(workspace_id),
            runs_count=self.runs.count_by_workspace_id(workspace_id),
            run_statuses=self._get_workspace_run_status_counters(workspace_id),
            metrics_count=self.metrics.count_by_workspace_id(workspace_id),
            events_count=self.events.count_by_workspace_id(workspace_id),
            artifacts_count=self.artifacts.count_by_workspace_id(workspace_id),
            storage_bytes=self.artifacts.sum_size_by_workspace_id(workspace_id),
        )

        return WorkspaceOverviewRead(
            workspace=WorkspaceRead.model_validate(workspace),
            counters=counters,
            projects=[ProjectRead.model_validate(project) for project in projects],
            recent_runs=[RunRead.model_validate(run) for run in recent_runs],
        )

    def get_project_overview(
            self,
            project_id: UUID,
            recent_runs_limit: int,
    ) -> ProjectOverviewRead:
        project = self.projects.get(project_id)
        if project is None:
            raise LookupError("Project not found")

        recent_runs = self.runs.list_recent_by_project_id(
            project_id=project_id,
            limit=recent_runs_limit,
        )

        counters = ProjectOverviewCounters(
            runs_count=self.runs.count_by_project_id(project_id),
            run_statuses=self._get_project_run_status_counters(project_id),
            metrics_count=self.metrics.count_by_project_id(project_id),
            events_count=self.events.count_by_project_id(project_id),
            artifacts_count=self.artifacts.count_by_project_id(project_id),
            storage_bytes=self.artifacts.sum_size_by_project_id(project_id),
        )

        return ProjectOverviewRead(
            project=ProjectRead.model_validate(project),
            counters=counters,
            recent_runs=[RunRead.model_validate(run) for run in recent_runs],
        )

    def _get_workspace_run_status_counters(self, workspace_id: UUID) -> RunStatusCounters:
        return RunStatusCounters(
            created=self.runs.count_by_workspace_id_and_status(
                workspace_id=workspace_id,
                status=RunStatus.CREATED.value,
            ),
            running=self.runs.count_by_workspace_id_and_status(
                workspace_id=workspace_id,
                status=RunStatus.RUNNING.value,
            ),
            finished=self.runs.count_by_workspace_id_and_status(
                workspace_id=workspace_id,
                status=RunStatus.FINISHED.value,
            ),
            failed=self.runs.count_by_workspace_id_and_status(
                workspace_id=workspace_id,
                status=RunStatus.FAILED.value,
            ),
        )

    def _get_project_run_status_counters(self, project_id: UUID) -> RunStatusCounters:
        return RunStatusCounters(
            created=self.runs.count_by_project_id_and_status(
                project_id=project_id,
                status=RunStatus.CREATED.value,
            ),
            running=self.runs.count_by_project_id_and_status(
                project_id=project_id,
                status=RunStatus.RUNNING.value,
            ),
            finished=self.runs.count_by_project_id_and_status(
                project_id=project_id,
                status=RunStatus.FINISHED.value,
            ),
            failed=self.runs.count_by_project_id_and_status(
                project_id=project_id,
                status=RunStatus.FAILED.value,
            ),
        )
