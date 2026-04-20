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


class ApiTokenService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tokens = ApiTokenRepository(db)
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def create_token(self, workspace_id: UUID, data: ApiTokenCreate) -> tuple[ApiToken, str]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

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

    def list_workspace_tokens(self, workspace_id: UUID) -> list[ApiToken]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        return self.tokens.list_by_workspace_id(workspace_id)

    def revoke_token(self, token_id: UUID) -> ApiToken:
        token = self.tokens.get(token_id)
        if token is None:
            raise LookupError("API token not found")

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

        if token.expires_at is not None and token.expires_at <= datetime.now(timezone.utc):
            raise ValueError("API token is expired")

        token = self.tokens.touch_last_used_at(token)
        self.db.commit()
        self.db.refresh(token)

        return token
