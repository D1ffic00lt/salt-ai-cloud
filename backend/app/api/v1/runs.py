from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Run
from app.db.models.api_token import ApiToken
from app.schemas.artifact import ArtifactRead
from app.schemas.event import EventRead
from app.schemas.metric import MetricRead
from app.schemas.run import RunCreate, RunDetailsRead, RunRead, RunUpdate
from app.services.artifact_service import ArtifactService
from app.services.event_service import EventService
from app.services.metric_service import MetricService
from app.services.project_service import ProjectService
from app.services.run_service import RunService

router = APIRouter()


@router.post(
    "/projects/{project_id}/runs",
    response_model=RunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
        project_id: UUID,
        payload: RunCreate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Run:
    project_service = ProjectService(db)
    run_service = RunService(db)

    try:
        project = project_service.get_project(project_id)
        ensure_token_workspace(token, project.workspace_id)
        require_scope(token, "runs:write")

        if payload.created_by_id is None:
            payload = payload.model_copy(update={"created_by_id": token.user_id})

        return run_service.create_run(project_id=project_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/runs", response_model=list[RunRead])
def list_project_runs(
        project_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> list[Run]:
    project_service = ProjectService(db)
    run_service = RunService(db)

    try:
        project = project_service.get_project(project_id)
        ensure_token_workspace(token, project.workspace_id)
        require_scope(token, "runs:write")

        return run_service.list_project_runs(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=RunRead)
def get_run(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Run:
    service = RunService(db)

    try:
        run = service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return run
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/runs/{run_id}/details", response_model=RunDetailsRead)
def get_run_details(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> RunDetailsRead:
    run_service = RunService(db)
    metric_service = MetricService(db)
    event_service = EventService(db)
    artifact_service = ArtifactService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        metrics = metric_service.list_run_metrics(run_id)
        events = event_service.list_run_events(run_id)
        artifacts = artifact_service.list_run_artifacts(run_id)

        return RunDetailsRead(
            run=RunRead.model_validate(run),
            metrics=[MetricRead.model_validate(metric) for metric in metrics],
            events=[EventRead.model_validate(event) for event in events],
            artifacts=[ArtifactRead.model_validate(artifact) for artifact in artifacts],
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/runs/{run_id}", response_model=RunRead)
def update_run(
        run_id: UUID,
        payload: RunUpdate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Run:
    service = RunService(db)

    try:
        run = service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return service.update_run(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/runs/{run_id}/finish", response_model=RunRead)
def finish_run(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Run:
    service = RunService(db)

    try:
        run = service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return service.finish_run(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/runs/{run_id}/fail", response_model=RunRead)
def fail_run(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Run:
    service = RunService(db)

    try:
        run = service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return service.fail_run(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
