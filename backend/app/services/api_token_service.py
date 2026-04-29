from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.api_token import ApiToken
from app.infrastructure.tokens import (
    generate_api_token,
    get_token_prefix,
    hash_api_token,
)
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.api_token import ApiTokenCreate

TOKEN_MANAGEMENT_SCOPE = "tokens:write"


class ApiTokenService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tokens = ApiTokenRepository(db)
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def create_token(
            self,
            workspace_id: UUID,
            data: ApiTokenCreate,
            current_token: ApiToken | None = None,
    ) -> tuple[ApiToken, str]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        self._ensure_token_management_access(
            workspace_id=workspace_id,
            current_token=current_token,
            allow_bootstrap=True,
        )

        user = self.users.get(data.user_id)
        if user is None:
            raise LookupError("User not found")

        raw_token = generate_api_token()
        token_hash = hash_api_token(raw_token)
        token_prefix = get_token_prefix(raw_token)

        token = self.tokens.create(
            workspace_id=workspace_id,
            user_id=data.user_id,
            name=data.name,
            token_hash=token_hash,
            token_prefix=token_prefix,
            scopes=data.scopes,
            expires_at=data.expires_at,
        )

        self.db.commit()
        self.db.refresh(token)

        return token, raw_token

    def list_workspace_tokens(
            self,
            workspace_id: UUID,
            current_token: ApiToken,
    ) -> list[ApiToken]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        self._ensure_token_management_access(
            workspace_id=workspace_id,
            current_token=current_token,
            allow_bootstrap=False,
        )

        return self.tokens.list_by_workspace_id(workspace_id)

    def revoke_token(
            self,
            token_id: UUID,
            current_token: ApiToken,
    ) -> ApiToken:
        token = self.tokens.get(token_id)
        if token is None:
            raise LookupError("API token not found")

        self._ensure_token_management_access(
            workspace_id=token.workspace_id,
            current_token=current_token,
            allow_bootstrap=False,
        )

        if token.revoked_at is None:
            token = self.tokens.revoke(token)
            self.db.commit()
            self.db.refresh(token)

        return token

    def authenticate_token(self, raw_token: str) -> ApiToken:
        token_hash = hash_api_token(raw_token)
        token = self.tokens.get_by_hash(token_hash)

        if token is None:
            raise LookupError("Invalid API token")

        if token.revoked_at is not None:
            raise ValueError("API token is revoked")

        if self._is_token_expired(token):
            raise ValueError("API token is expired")

        token = self.tokens.touch_last_used_at(token)
        self.db.commit()
        self.db.refresh(token)

        return token

    def _ensure_token_management_access(
            self,
            workspace_id: UUID,
            current_token: ApiToken | None,
            allow_bootstrap: bool,
    ) -> None:
        if current_token is None:
            if allow_bootstrap and not self._workspace_has_active_tokens(workspace_id):
                return

            raise PermissionError("API token is required")

        if current_token.workspace_id != workspace_id:
            raise PermissionError("API token does not have access to this workspace")

        if not self._can_manage_tokens(current_token):
            raise PermissionError(f"Missing required scope: {TOKEN_MANAGEMENT_SCOPE}")

    def _workspace_has_active_tokens(self, workspace_id: UUID) -> bool:
        tokens = self.tokens.list_by_workspace_id(workspace_id)

        return any(self._is_active_token(token) for token in tokens)

    def _is_active_token(self, token: ApiToken) -> bool:
        if token.revoked_at is not None:
            return False

        return not self._is_token_expired(token)

    def _is_token_expired(self, token: ApiToken) -> bool:
        if token.expires_at is None:
            return False

        return self._as_utc(token.expires_at) <= datetime.now(timezone.utc)

    def _can_manage_tokens(self, token: ApiToken) -> bool:
        scopes = token.scopes or []

        if "*" in scopes:
            return True

        if TOKEN_MANAGEMENT_SCOPE in scopes:
            return True

        return "runs:write" in scopes and "artifacts:write" in scopes

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)
