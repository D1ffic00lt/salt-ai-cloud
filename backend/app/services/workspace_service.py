from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.workspace import Workspace
from app.domain.enums import WorkspaceRole
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def create_workspace(self, data: WorkspaceCreate) -> Workspace:
        owner = self.users.get(data.owner_user_id)
        if owner is None:
            raise LookupError("Owner user not found")

        existing_workspace = self.workspaces.get_by_slug(data.slug)
        if existing_workspace is not None:
            raise ValueError("Workspace slug already exists")

        workspace = self.workspaces.create(
            name=data.name,
            slug=data.slug,
            owner_user_id=data.owner_user_id,
            plan_id=data.plan_id,
        )
        self.workspaces.add_member(
            workspace_id=workspace.id,
            user_id=data.owner_user_id,
            role=WorkspaceRole.OWNER.value,
        )
        self.workspaces.create_quota(workspace_id=workspace.id)

        self.db.commit()
        self.db.refresh(workspace)

        return workspace

    def list_workspaces(self, owner_user_id: UUID | None = None) -> list[Workspace]:
        return self.workspaces.list(owner_user_id=owner_user_id)

    def get_workspace(self, workspace_id: UUID) -> Workspace:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        return workspace
