from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
        payload: WorkspaceCreate,
        db: Session = Depends(get_db),
) -> Workspace:
    service = WorkspaceService(db)

    try:
        return service.create_workspace(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(
        owner_user_id: UUID | None = Query(default=None),
        db: Session = Depends(get_db),
) -> list[Workspace]:
    service = WorkspaceService(db)
    return service.list_workspaces(owner_user_id=owner_user_id)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(
        workspace_id: UUID,
        db: Session = Depends(get_db),
) -> Workspace:
    service = WorkspaceService(db)

    try:
        return service.get_workspace(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
