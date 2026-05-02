from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models.api_token import ApiToken
from app.schemas.overview import ProjectOverviewRead, WorkspaceOverviewRead
from app.services.overview_service import OverviewService
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.get("/overview", response_model=WorkspaceOverviewRead)
def get_current_workspace_overview(
        recent_runs_limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> WorkspaceOverviewRead:
    overview_service = OverviewService(db)

    require_scope(token, "workspaces:read")
    require_scope(token, "projects:read")
    require_scope(token, "runs:read")

    return overview_service.get_workspace_overview(
        workspace_id=token.workspace_id,
        recent_runs_limit=recent_runs_limit,
    )


@router.get("/workspaces/{workspace_id}/overview", response_model=WorkspaceOverviewRead)
def get_workspace_overview(
        workspace_id: UUID,
        recent_runs_limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> WorkspaceOverviewRead:
    workspace_service = WorkspaceService(db)
    overview_service = OverviewService(db)

    try:
        workspace = workspace_service.get_workspace(workspace_id)
        ensure_token_workspace(token, workspace.id)
        require_scope(token, "workspaces:read")
        require_scope(token, "projects:read")
        require_scope(token, "runs:read")

        return overview_service.get_workspace_overview(
            workspace_id=workspace_id,
            recent_runs_limit=recent_runs_limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/overview", response_model=ProjectOverviewRead)
def get_project_overview(
        project_id: UUID,
        recent_runs_limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> ProjectOverviewRead:
    project_service = ProjectService(db)
    overview_service = OverviewService(db)

    try:
        project = project_service.get_project(project_id)
        ensure_token_workspace(token, project.workspace_id)
        require_scope(token, "projects:read")
        require_scope(token, "runs:read")

        return overview_service.get_project_overview(
            project_id=project_id,
            recent_runs_limit=recent_runs_limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
