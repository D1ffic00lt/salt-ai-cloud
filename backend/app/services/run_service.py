from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.run import Run
from app.domain.enums import RunStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.repositories.user_repository import UserRepository
from app.schemas.run import RunCreate, RunUpdate


class RunService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.projects = ProjectRepository(db)
        self.runs = RunRepository(db)

    def create_run(self, project_id: UUID, data: RunCreate) -> Run:
        project = self.projects.get(project_id)
        if project is None:
            raise LookupError("Project not found")

        if data.created_by_id is not None:
            user = self.users.get(data.created_by_id)
            if user is None:
                raise LookupError("Creator user not found")

        run = self.runs.create(
            workspace_id=project.workspace_id,
            project_id=project.id,
            created_by_id=data.created_by_id,
            name=data.name,
            status=RunStatus.RUNNING.value,
            config=data.config,
            manifest=data.manifest,
            tags=data.tags,
            started_at=datetime.now(timezone.utc),
        )

        self.db.commit()
        self.db.refresh(run)

        return run

    def list_project_runs(self, project_id: UUID) -> list[Run]:
        project = self.projects.get(project_id)
        if project is None:
            raise LookupError("Project not found")

        return self.runs.list_by_project_id(project_id)

    def get_run(self, run_id: UUID) -> Run:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        return run

    def update_run(self, run_id: UUID, data: RunUpdate) -> Run:
        run = self.get_run(run_id)

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Finished or failed run cannot be updated")

        run = self.runs.update(
            run=run,
            name=data.name,
            config=data.config,
            manifest=data.manifest,
            tags=data.tags,
        )

        self.db.commit()
        self.db.refresh(run)

        return run

    def finish_run(self, run_id: UUID) -> Run:
        run = self.get_run(run_id)

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Run is already completed")

        run.status = RunStatus.FINISHED.value
        run.finished_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(run)

        return run

    def fail_run(self, run_id: UUID) -> Run:
        run = self.get_run(run_id)

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Run is already completed")

        run.status = RunStatus.FAILED.value
        run.finished_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(run)

        return run
