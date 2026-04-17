from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.run import RunCreate, RunRead, RunUpdate
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
) -> RunRead:
    service = RunService(db)

    try:
        return service.create_run(project_id=project_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/runs", response_model=list[RunRead])
def list_project_runs(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> list[RunRead]:
    service = RunService(db)

    try:
        return service.list_project_runs(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=RunRead)
def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> RunRead:
    service = RunService(db)

    try:
        return service.get_run(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/runs/{run_id}", response_model=RunRead)
def update_run(
    run_id: UUID,
    payload: RunUpdate,
    db: Session = Depends(get_db),
) -> RunRead:
    service = RunService(db)

    try:
        return service.update_run(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/runs/{run_id}/finish", response_model=RunRead)
def finish_run(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> RunRead:
    service = RunService(db)

    try:
        return service.finish_run(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/runs/{run_id}/fail", response_model=RunRead)
def fail_run(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> RunRead:
    service = RunService(db)

    try:
        return service.fail_run(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc