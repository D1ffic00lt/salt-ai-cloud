from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.api_token import ApiToken
from app.db.session import SessionLocal
from app.services.api_token_service import ApiTokenService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_api_token(
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
) -> ApiToken:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    return _authenticate_authorization_header(authorization=authorization, db=db)


def get_optional_current_api_token(
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
) -> ApiToken | None:
    if authorization is None:
        return None

    return _authenticate_authorization_header(authorization=authorization, db=db)


def ensure_token_workspace(token: ApiToken, workspace_id: UUID) -> None:
    if token.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token does not have access to this workspace",
        )


def require_scope(token: ApiToken, scope: str) -> None:
    scopes = token.scopes or []

    if "*" in scopes:
        return

    if scope not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required scope: {scope}",
        )


def _authenticate_authorization_header(authorization: str, db: Session) -> ApiToken:
    scheme, _, token = authorization.partition(" ")

    token = token.strip()

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )

    service = ApiTokenService(db)

    try:
        return service.authenticate_token(token)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc