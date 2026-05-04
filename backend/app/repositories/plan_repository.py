from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.plan import Plan


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, plan_id: UUID) -> Plan | None:
        statement = select(Plan).where(Plan.id == plan_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_code(self, code: str) -> Plan | None:
        statement = select(Plan).where(Plan.code == code)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self) -> list[Plan]:
        statement = select(Plan).order_by(Plan.created_at.asc())
        return list(self.db.execute(statement).scalars().all())

    def create(
            self,
            code: str,
            name: str,
            max_projects: int | None = None,
            max_runs: int | None = None,
            max_artifacts: int | None = None,
            max_storage_bytes: int | None = None,
    ) -> Plan:
        plan = Plan(
            code=code,
            name=name,
            max_projects=max_projects,
            max_runs=max_runs,
            max_artifacts=max_artifacts,
            max_storage_bytes=max_storage_bytes,
        )

        self.db.add(plan)
        self.db.flush()

        return plan

    def update(
            self,
            plan: Plan,
            name: str,
            max_projects: int | None = None,
            max_runs: int | None = None,
            max_artifacts: int | None = None,
            max_storage_bytes: int | None = None,
    ) -> Plan:
        plan.name = name
        plan.max_projects = max_projects
        plan.max_runs = max_runs
        plan.max_artifacts = max_artifacts
        plan.max_storage_bytes = max_storage_bytes

        self.db.flush()

        return plan

    def upsert(
            self,
            code: str,
            name: str,
            max_projects: int | None = None,
            max_runs: int | None = None,
            max_artifacts: int | None = None,
            max_storage_bytes: int | None = None,
    ) -> Plan:
        plan = self.get_by_code(code)

        if plan is None:
            return self.create(
                code=code,
                name=name,
                max_projects=max_projects,
                max_runs=max_runs,
                max_artifacts=max_artifacts,
                max_storage_bytes=max_storage_bytes,
            )

        return self.update(
            plan=plan,
            name=name,
            max_projects=max_projects,
            max_runs=max_runs,
            max_artifacts=max_artifacts,
            max_storage_bytes=max_storage_bytes,
        )
