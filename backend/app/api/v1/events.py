from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Event
from app.db.models.api_token import ApiToken
from app.schemas.event import EventCreate, EventRead
from app.services.event_service import EventService
from app.services.run_service import RunService

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
        token: ApiToken = Depends(get_current_api_token),
) -> Event:
    run_service = RunService(db)
    event_service = EventService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "runs:write")

        return event_service.create_event(run_id=run_id, data=payload)
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
