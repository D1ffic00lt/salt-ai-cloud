from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.run import Run


class RunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, run_id: UUID) -> Run | None:
        statement = select(Run).where(Run.id == run_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list_by_project_id(self, project_id: UUID) -> list[Run]:
        statement = (
            select(Run)
            .where(Run.project_id == project_id)
            .order_by(Run.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create(
            self,
            workspace_id: UUID,
            project_id: UUID,
            status: str,
            started_at: datetime,
            name: str | None = None,
            config: dict | None = None,
            manifest: dict | None = None,
            tags: list[str] | None = None,
            created_by_id: UUID | None = None,
    ) -> Run:
        run = Run(
            workspace_id=workspace_id,
            project_id=project_id,
            created_by_id=created_by_id,
            name=name,
            status=status,
            config=config or {},
            manifest=manifest or {},
            tags=tags or [],
            started_at=started_at,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def update(
            self,
            run: Run,
            name: str | None = None,
            config: dict | None = None,
            manifest: dict | None = None,
            tags: list[str] | None = None,
    ) -> Run:
        if name is not None:
            run.name = name

        if config is not None:
            run.config = config

        if manifest is not None:
            run.manifest = manifest

        if tags is not None:
            run.tags = tags

        self.db.flush()
        return run
