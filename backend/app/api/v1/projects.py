from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Project
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
        workspace_id: UUID,
        payload: ProjectCreate,
        db: Session = Depends(get_db),
) -> Project:
    service = ProjectService(db)

    try:
        return service.create_project(workspace_id=workspace_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectRead])
def list_workspace_projects(
        workspace_id: UUID,
        db: Session = Depends(get_db),
) -> list[Project]:
    service = ProjectService(db)

    try:
        return service.list_workspace_projects(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
        project_id: UUID,
        db: Session = Depends(get_db),
) -> Project:
    service = ProjectService(db)

    try:
        return service.get_project(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
