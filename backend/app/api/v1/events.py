from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Event
from app.schemas.event import EventCreate, EventRead
from app.services.event_service import EventService

router = APIRouter()


@router.post(
    "/runs/{run_id}/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
        run_id: UUID,
        payload: EventCreate,
        db: Session = Depends(get_db),
) -> Event:
    service = EventService(db)

    try:
        return service.create_event(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}/events", response_model=list[EventRead])
def list_run_events(
        run_id: UUID,
        db: Session = Depends(get_db),
) -> list[Event]:
    service = EventService(db)

    try:
        return service.list_run_events(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
