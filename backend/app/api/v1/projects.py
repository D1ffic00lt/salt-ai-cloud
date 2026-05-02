from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Project
from app.db.models.api_token import ApiToken
from app.schemas.project import ProjectCreate, ProjectDetailsRead, ProjectRead
from app.schemas.run import RunRead
from app.services.project_service import ProjectService
from app.services.run_service import RunService

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
        token: ApiToken = Depends(get_current_api_token),
) -> Project:
    ensure_token_workspace(token, workspace_id)
    require_scope(token, "projects:write")

    if payload.created_by_id is not None and payload.created_by_id != token.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project creator must match current API token user",
        )

    payload = payload.model_copy(update={"created_by_id": token.user_id})

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
        token: ApiToken = Depends(get_current_api_token),
) -> list[Project]:
    ensure_token_workspace(token, workspace_id)
    require_scope(token, "projects:read")

    service = ProjectService(db)

    try:
        return service.list_workspace_projects(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
        project_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Project:
    service = ProjectService(db)

    try:
        project = service.get_project(project_id)
        ensure_token_workspace(token, project.workspace_id)
        require_scope(token, "projects:read")

        return project
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/details", response_model=ProjectDetailsRead)
def get_project_details(
        project_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> ProjectDetailsRead:
    project_service = ProjectService(db)
    run_service = RunService(db)

    try:
        project = project_service.get_project(project_id)
        ensure_token_workspace(token, project.workspace_id)
        require_scope(token, "projects:read")
        require_scope(token, "runs:read")

        runs = run_service.list_project_runs(project_id)

        return ProjectDetailsRead(
            project=ProjectRead.model_validate(project),
            runs=[RunRead.model_validate(run) for run in runs],
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
