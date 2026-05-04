from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.plan import Plan
from app.db.models.workspace import Workspace
from app.repositories.plan_repository import PlanRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.plan import PlanCreate, WorkspacePlanUpdate

DEFAULT_PLANS = [
    PlanCreate(
        code="free",
        name="Free",
        max_projects=3,
        max_runs=1000,
        max_artifacts=1000,
        max_storage_bytes=1_073_741_824,
    ),
    PlanCreate(
        code="pro",
        name="Pro",
        max_projects=50,
        max_runs=100_000,
        max_artifacts=100_000,
        max_storage_bytes=107_374_182_400,
    ),
    PlanCreate(
        code="unlimited",
        name="Unlimited",
        max_projects=None,
        max_runs=None,
        max_artifacts=None,
        max_storage_bytes=None,
    ),
]


class PlanService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.plans = PlanRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def list_plans(self) -> list[Plan]:
        return self.plans.list()

    def create_or_update_plan(self, data: PlanCreate) -> Plan:
        plan = self.plans.upsert(
            code=data.code,
            name=data.name,
            max_projects=data.max_projects,
            max_runs=data.max_runs,
            max_artifacts=data.max_artifacts,
            max_storage_bytes=data.max_storage_bytes,
        )

        self.db.commit()
        self.db.refresh(plan)

        return plan

    def seed_default_plans(self) -> list[Plan]:
        plans = [
            self.plans.upsert(
                code=data.code,
                name=data.name,
                max_projects=data.max_projects,
                max_runs=data.max_runs,
                max_artifacts=data.max_artifacts,
                max_storage_bytes=data.max_storage_bytes,
            )
            for data in DEFAULT_PLANS
        ]

        self.db.commit()

        for plan in plans:
            self.db.refresh(plan)

        return plans

    def assign_workspace_plan(
            self,
            workspace_id: UUID,
            data: WorkspacePlanUpdate,
    ) -> Workspace:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise LookupError("Workspace not found")

        if data.plan_id is not None:
            plan = self.plans.get(data.plan_id)
            if plan is None:
                raise LookupError("Plan not found")

        workspace.plan_id = data.plan_id

        self.db.commit()
        self.db.refresh(workspace)

        return workspace
