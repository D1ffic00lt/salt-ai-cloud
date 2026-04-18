from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.event import Event
from app.domain.enums import RunStatus
from app.repositories.event_repository import EventRepository
from app.repositories.run_repository import RunRepository
from app.schemas.event import EventCreate


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.runs = RunRepository(db)
        self.events = EventRepository(db)

    def create_event(self, run_id: UUID, data: EventCreate) -> Event:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        if run.status in {RunStatus.FINISHED.value, RunStatus.FAILED.value}:
            raise ValueError("Completed run cannot accept events")

        event = self.events.create(
            workspace_id=run.workspace_id,
            run_id=run.id,
            type_=data.type,
            level=data.level,
            message=data.message,
            payload=data.payload,
            timestamp=data.timestamp,
        )

        self.db.commit()
        self.db.refresh(event)

        return event

    def list_run_events(self, run_id: UUID) -> list[Event]:
        run = self.runs.get(run_id)
        if run is None:
            raise LookupError("Run not found")

        return self.events.list_by_run_id(run_id)
