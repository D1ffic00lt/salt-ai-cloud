from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.metric import Metric
from app.db.models.run import Run


class MetricRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_run_id(self, run_id: UUID) -> list[Metric]:
        statement = (
            select(Metric)
            .where(Metric.run_id == run_id)
            .order_by(Metric.timestamp.asc(), Metric.created_at.asc())
        )
        return list(self.db.execute(statement).scalars().all())

    def count_by_workspace_id(self, workspace_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Metric)
            .where(Metric.workspace_id == workspace_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def count_by_project_id(self, project_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Metric)
            .join(Run, Metric.run_id == Run.id)
            .where(Run.project_id == project_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def create(
            self,
            workspace_id: UUID,
            run_id: UUID,
            key: str,
            value: float,
            step: int | None = None,
            payload: dict | None = None,
            timestamp: datetime | None = None,
    ) -> Metric:
        metric = Metric(
            workspace_id=workspace_id,
            run_id=run_id,
            key=key,
            value=value,
            step=step,
            payload=payload or {},
        )

        if timestamp is not None:
            metric.timestamp = timestamp

        self.db.add(metric)
        self.db.flush()
        return metric
