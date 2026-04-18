from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Metric
from app.schemas.metric import MetricCreate, MetricRead
from app.services.metric_service import MetricService

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
) -> Metric:
    service = MetricService(db)

    try:
        return service.create_metric(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}/metrics", response_model=list[MetricRead])
def list_run_metrics(
        run_id: UUID,
        db: Session = Depends(get_db),
) -> list[Metric]:
    service = MetricService(db)

    try:
        return service.list_run_metrics(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
