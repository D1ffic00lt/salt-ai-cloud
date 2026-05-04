from fastapi import APIRouter

from app.api.v1.api_tokens import router as api_tokens_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.overview import router as overview_router
from app.api.v1.plans import router as plans_router
from app.api.v1.projects import router as projects_router
from app.api.v1.runs import router as runs_router
from app.api.v1.workspaces import router as workspaces_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["system"])
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(runs_router, tags=["runs"])
api_router.include_router(metrics_router, tags=["metrics"])
api_router.include_router(events_router, tags=["events"])
api_router.include_router(artifacts_router, tags=["artifacts"])
api_router.include_router(overview_router, tags=["overview"])
api_router.include_router(api_tokens_router, tags=["api-tokens"])
api_router.include_router(plans_router, tags=["plans"])
