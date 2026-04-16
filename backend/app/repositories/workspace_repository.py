from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.quota import Quota
from app.db.models.workspace import Workspace, WorkspaceMember


class WorkspaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, workspace_id: UUID) -> Workspace | None:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Workspace | None:
        statement = select(Workspace).where(Workspace.slug == slug)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self, owner_user_id: UUID | None = None) -> list[Workspace]:
        statement = select(Workspace).order_by(Workspace.created_at.desc())

        if owner_user_id is not None:
            statement = statement.where(Workspace.owner_user_id == owner_user_id)

        return list(self.db.execute(statement).scalars().all())

    def create(
            self,
            name: str,
            slug: str,
            owner_user_id: UUID,
            plan_id: UUID | None = None,
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            slug=slug,
            owner_user_id=owner_user_id,
            plan_id=plan_id,
        )
        self.db.add(workspace)
        self.db.flush()
        return workspace

    def add_member(
            self,
            workspace_id: UUID,
            user_id: UUID,
            role: str,
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def create_quota(self, workspace_id: UUID) -> Quota:
        quota = Quota(workspace_id=workspace_id)
        self.db.add(quota)
        self.db.flush()
        return quota
