from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_api_token,
    get_db,
    get_optional_current_api_token,
)
from app.db.models.api_token import ApiToken
from app.schemas.api_token import (
    ApiTokenCreate,
    ApiTokenCreated,
    ApiTokenRead,
    CurrentApiUser,
)
from app.services.api_token_service import ApiTokenService

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/api-tokens",
    response_model=ApiTokenCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_api_token(
        workspace_id: UUID,
        payload: ApiTokenCreate,
        db: Session = Depends(get_db),
        current_token: ApiToken | None = Depends(get_optional_current_api_token),
) -> ApiTokenCreated:
    service = ApiTokenService(db)

    try:
        token, raw_token = service.create_token(
            workspace_id=workspace_id,
            data=payload,
            current_token=current_token,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ApiTokenCreated(
        id=token.id,
        workspace_id=token.workspace_id,
        user_id=token.user_id,
        name=token.name,
        token=raw_token,
        token_prefix=token.token_prefix,
        scopes=token.scopes,
        expires_at=token.expires_at,
        created_at=token.created_at,
    )


@router.get("/workspaces/{workspace_id}/api-tokens", response_model=list[ApiTokenRead])
def list_workspace_api_tokens(
        workspace_id: UUID,
        db: Session = Depends(get_db),
        current_token: ApiToken = Depends(get_current_api_token),
) -> list[ApiToken]:
    service = ApiTokenService(db)

    try:
        return service.list_workspace_tokens(
            workspace_id=workspace_id,
            current_token=current_token,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/api-tokens/{token_id}", response_model=ApiTokenRead)
def delete_api_token(
        token_id: UUID,
        db: Session = Depends(get_db),
        current_token: ApiToken = Depends(get_current_api_token),
) -> ApiToken:
    return _revoke_api_token(
        token_id=token_id,
        db=db,
        current_token=current_token,
    )


@router.post("/api-tokens/{token_id}/revoke", response_model=ApiTokenRead)
def revoke_api_token(
        token_id: UUID,
        db: Session = Depends(get_db),
        current_token: ApiToken = Depends(get_current_api_token),
) -> ApiToken:
    return _revoke_api_token(
        token_id=token_id,
        db=db,
        current_token=current_token,
    )


@router.get("/auth/me", response_model=CurrentApiUser)
def get_current_user_from_api_token(
        token: ApiToken = Depends(get_current_api_token),
) -> CurrentApiUser:
    return CurrentApiUser(
        user_id=token.user_id,
        workspace_id=token.workspace_id,
        token_id=token.id,
        scopes=token.scopes,
    )


def _revoke_api_token(
        token_id: UUID,
        db: Session,
        current_token: ApiToken,
) -> ApiToken:
    service = ApiTokenService(db)

    try:
        return service.revoke_token(
            token_id=token_id,
            current_token=current_token,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
