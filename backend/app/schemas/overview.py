from pydantic import BaseModel, Field

from app.schemas.project import ProjectRead
from app.schemas.run import RunRead
from app.schemas.workspace import WorkspaceRead


class RunStatusCounters(BaseModel):
    created: int = 0
    running: int = 0
    finished: int = 0
    failed: int = 0


class WorkspaceOverviewCounters(BaseModel):
    projects_count: int = 0
    runs_count: int = 0
    run_statuses: RunStatusCounters = Field(default_factory=RunStatusCounters)
    metrics_count: int = 0
    events_count: int = 0
    artifacts_count: int = 0
    storage_bytes: int = 0


class ProjectOverviewCounters(BaseModel):
    runs_count: int = 0
    run_statuses: RunStatusCounters = Field(default_factory=RunStatusCounters)
    metrics_count: int = 0
    events_count: int = 0
    artifacts_count: int = 0
    storage_bytes: int = 0


class WorkspaceOverviewRead(BaseModel):
    workspace: WorkspaceRead
    counters: WorkspaceOverviewCounters
    projects: list[ProjectRead] = Field(default_factory=list)
    recent_runs: list[RunRead] = Field(default_factory=list)


class ProjectOverviewRead(BaseModel):
    project: ProjectRead
    counters: ProjectOverviewCounters
    recent_runs: list[RunRead] = Field(default_factory=list)
