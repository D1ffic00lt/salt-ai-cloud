from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Metric
from app.db.models.api_token import ApiToken
from app.schemas.metric import MetricCreate, MetricRead
from app.services.metric_service import MetricService
from app.services.run_service import RunService

router = APIRouter()


@router.post(
    "/runs/{run_id}/metrics",
    response_model=MetricRead,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
        run_id: UUID,
        payload: MetricCreate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Metric:
    run_service = RunService(db)
    metric_service = MetricService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return metric_service.create_metric(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}/metrics", response_model=list[MetricRead])
def list_run_metrics(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> list[Metric]:
    run_service = RunService(db)
    metric_service = MetricService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return metric_service.list_run_metrics(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
