from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.metric import Metric
from app.domain.enums import RunStatus
from app.repositories.metric_repository import MetricRepository
from app.repositories.run_repository import RunRepository
from app.schemas.metric import MetricCreate


class MetricService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.runs = RunRepository(db)
        self.metrics = MetricRepository(db)

    def create_metric(self, run_id: UUID, data: MetricCreate) -> Metric:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Completed run cannot accept metrics")

        metric = self.metrics.create(
            workspace_id=run.workspace_id,
            run_id=run.id,
            key=data.key,
            value=data.value,
            step=data.step,
            payload=data.payload,
            timestamp=data.timestamp,
        )

        self.db.commit()
        self.db.refresh(metric)

        return metric

    def list_run_metrics(self, run_id: UUID) -> list[Metric]:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        return self.metrics.list_by_run_id(run_id)
