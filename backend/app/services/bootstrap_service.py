from sqlalchemy.orm import Session

from app.db.models.api_token import ApiToken
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.repositories.user_repository import UserRepository
from app.schemas.api_token import ApiTokenCreate, BootstrapCreate
from app.schemas.workspace import WorkspaceCreate
from app.services.api_token_service import ApiTokenService
from app.services.workspace_service import WorkspaceService


class BootstrapService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceService(db)
        self.tokens = ApiTokenService(db)

    def bootstrap(self, data: BootstrapCreate) -> tuple[User, Workspace, ApiToken, str]:
        user = self._get_or_create_user(data)

        workspace = self.workspaces.create_workspace(
            WorkspaceCreate(
                name=data.workspace_name,
                slug=data.workspace_slug,
                owner_user_id=user.id,
                plan_id=data.plan_id,
            )
        )

        token, raw_token = self.tokens.create_bootstrap_token(
            workspace_id=workspace.id,
            data=ApiTokenCreate(
                name=data.token_name,
                user_id=user.id,
                scopes=data.scopes,
                expires_at=data.expires_at,
            ),
        )

        return user, workspace, token, raw_token

    def _get_or_create_user(self, data: BootstrapCreate) -> User:
        if data.telegram_id is not None:
            existing_user = self.users.get_by_telegram_id(data.telegram_id)
            if existing_user is not None:
                return existing_user

        user = self.users.create(
            telegram_id=data.telegram_id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        self.db.commit()
        self.db.refresh(user)

        return user
