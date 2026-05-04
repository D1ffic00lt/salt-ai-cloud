from secrets import compare_digest
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.core.config import get_settings
from app.db.models.api_token import ApiToken
from app.db.models.plan import Plan
from app.db.models.workspace import Workspace
from app.schemas.plan import PlanCreate, PlanRead, WorkspacePlanUpdate
from app.schemas.workspace import WorkspaceRead
from app.services.plan_service import PlanService

router = APIRouter()


@router.get("/plans", response_model=list[PlanRead])
def list_plans(
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> list[Plan]:
    require_scope(token, "workspaces:read")

    service = PlanService(db)

    return service.list_plans()


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_or_update_plan(
        payload: PlanCreate,
        setup_key: str | None = Header(default=None, alias="X-SaltAI-Setup-Key"),
        db: Session = Depends(get_db),
) -> Plan:
    _ensure_setup_key(setup_key)

    service = PlanService(db)

    return service.create_or_update_plan(payload)


@router.post("/plans/seed-defaults", response_model=list[PlanRead])
def seed_default_plans(
        setup_key: str | None = Header(default=None, alias="X-SaltAI-Setup-Key"),
        db: Session = Depends(get_db),
) -> list[Plan]:
    _ensure_setup_key(setup_key)

    service = PlanService(db)

    return service.seed_default_plans()


@router.patch("/workspaces/{workspace_id}/plan", response_model=WorkspaceRead)
def assign_workspace_plan(
        workspace_id: UUID,
        payload: WorkspacePlanUpdate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Workspace:
    ensure_token_workspace(token, workspace_id)
    require_scope(token, "workspaces:write")

    service = PlanService(db)

    try:
        return service.assign_workspace_plan(
            workspace_id=workspace_id,
            data=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _ensure_setup_key(setup_key: str | None) -> None:
    settings = get_settings()

    if settings.bootstrap_setup_key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap setup key is not configured",
        )

    if setup_key is None or not compare_digest(setup_key, settings.bootstrap_setup_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid bootstrap setup key",
        )
