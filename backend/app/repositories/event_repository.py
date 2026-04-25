from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.event import Event
from app.db.models.run import Run


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_run_id(self, run_id: UUID) -> list[Event]:
        statement = (
            select(Event)
            .where(Event.run_id == run_id)
            .order_by(Event.timestamp.asc(), Event.created_at.asc())
        )
        return list(self.db.execute(statement).scalars().all())

    def count_by_workspace_id(self, workspace_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Event)
            .where(Event.workspace_id == workspace_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def count_by_project_id(self, project_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Event)
            .join(Run, Event.run_id == Run.id)
            .where(Run.project_id == project_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def create(
            self,
            workspace_id: UUID,
            run_id: UUID,
            type_: str,
            level: str,
            message: str | None = None,
            payload: dict | None = None,
            timestamp: datetime | None = None,
    ) -> Event:
        event = Event(
            workspace_id=workspace_id,
            run_id=run_id,
            type=type_,
            level=level,
            message=message,
            payload=payload or {},
        )

        if timestamp is not None:
            event.timestamp = timestamp

        self.db.add(event)
        self.db.flush()
        return event
