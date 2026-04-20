from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.api_token import ApiToken


class ApiTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, token_id: UUID) -> ApiToken | None:
        statement = select(ApiToken).where(ApiToken.id == token_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_hash(self, token_hash: str) -> ApiToken | None:
        statement = select(ApiToken).where(ApiToken.token_hash == token_hash)
        return self.db.execute(statement).scalar_one_or_none()

    def list_by_workspace_id(self, workspace_id: UUID) -> list[ApiToken]:
        statement = (
            select(ApiToken)
            .where(ApiToken.workspace_id == workspace_id)
            .order_by(ApiToken.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create(
            self,
            workspace_id: UUID,
            user_id: UUID,
            name: str,
            token_hash: str,
            token_prefix: str,
            scopes: list[str],
            expires_at: datetime | None,
    ) -> ApiToken:
        token = ApiToken(
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            token_hash=token_hash,
            token_prefix=token_prefix,
            scopes=scopes,
            expires_at=expires_at,
        )

        self.db.add(token)
        self.db.flush()
        return token

    def touch_last_used_at(self, token: ApiToken) -> ApiToken:
        token.last_used_at = datetime.now(timezone.utc)
        self.db.flush()
        return token

    def revoke(self, token: ApiToken) -> ApiToken:
        token.revoked_at = datetime.now(timezone.utc)
        self.db.flush()
        return token
