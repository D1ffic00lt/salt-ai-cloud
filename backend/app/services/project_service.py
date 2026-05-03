from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.project import ProjectCreate
from app.services.quota_service import QuotaService


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.projects = ProjectRepository(db)
        self.quotas = QuotaService(db)

    def create_project(self, workspace_id: UUID, data: ProjectCreate) -> Project:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        if data.created_by_id is not None:
            user = self.users.get(data.created_by_id)
            if user is None:
                raise LookupError("Creator user not found")

        existing_project = self.projects.get_by_workspace_and_name(
            workspace_id=workspace_id,
            name=data.name,
        )
        if existing_project is not None:
            raise ValueError("Project with this name already exists in workspace")

        self.quotas.ensure_can_create_project(workspace_id)

        project = self.projects.create(
            workspace_id=workspace_id,
            name=data.name,
            description=data.description,
            created_by_id=data.created_by_id,
        )

        self.quotas.refresh_workspace_quota(workspace_id)

        self.db.commit()
        self.db.refresh(project)

        return project

    def list_workspace_projects(self, workspace_id: UUID) -> list[Project]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        return self.projects.list_by_workspace_id(workspace_id)

    def get_project(self, project_id: UUID) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise LookupError("Project not found")

        return project
