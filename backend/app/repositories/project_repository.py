from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: UUID) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_workspace_and_name(self, workspace_id: UUID, name: str) -> Project | None:
        statement = select(Project).where(
            Project.workspace_id == workspace_id,
            Project.name == name,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list_by_workspace_id(self, workspace_id: UUID) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create(
            self,
            workspace_id: UUID,
            name: str,
            description: str | None = None,
            created_by_id: UUID | None = None,
    ) -> Project:
        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
            created_by_id=created_by_id,
        )
        self.db.add(project)
        self.db.flush()
        return project
