from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Workspace
from app.db.models.api_token import ApiToken
from app.schemas.project import ProjectRead
from app.schemas.workspace import WorkspaceCreate, WorkspaceDetailsRead, WorkspaceRead
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
        payload: WorkspaceCreate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Workspace:
    require_scope(token, "workspaces:write")

    if payload.owner_user_id is not None and payload.owner_user_id != token.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace owner must match current API token user",
        )

    payload = payload.model_copy(update={"owner_user_id": token.user_id})

    service = WorkspaceService(db)

    try:
        return service.create_workspace(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> list[Workspace]:
    require_scope(token, "workspaces:read")

    service = WorkspaceService(db)

    try:
        return [service.get_workspace(token.workspace_id)]
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(
        workspace_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Workspace:
    ensure_token_workspace(token, workspace_id)
    require_scope(token, "workspaces:read")

    service = WorkspaceService(db)

    try:
        return service.get_workspace(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workspace_id}/details", response_model=WorkspaceDetailsRead)
def get_workspace_details(
        workspace_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> WorkspaceDetailsRead:
    ensure_token_workspace(token, workspace_id)
    require_scope(token, "workspaces:read")
    require_scope(token, "projects:read")

    workspace_service = WorkspaceService(db)
    project_service = ProjectService(db)

    try:
        workspace = workspace_service.get_workspace(workspace_id)
        projects = project_service.list_workspace_projects(workspace_id)

        return WorkspaceDetailsRead(
            workspace=WorkspaceRead.model_validate(workspace),
            projects=[ProjectRead.model_validate(project) for project in projects],
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
