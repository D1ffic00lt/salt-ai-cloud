export type Workspace = {
  id: string;
  name: string;
  slug: string;
  owner_user_id: string;
  plan_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  workspace_id: string;
  created_by_id: string | null;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectCreatePayload = {
  name: string;
  description: string | null;
};

export type Run = {
  id: string;
  workspace_id: string;
  project_id: string;
  created_by_id: string | null;
  name: string | null;
  status: string;
  config: Record<string, unknown>;
  manifest: Record<string, unknown>;
  tags: string[];
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Metric = {
  id: string;
  workspace_id: string;
  run_id: string;
  key: string;
  value: number;
  step: number | null;
  payload: Record<string, unknown>;
  timestamp: string;
  created_at: string;
};

export type Event = {
  id: string;
  workspace_id: string;
  run_id: string;
  type: string;
  level: string;
  message: string | null;
  payload: Record<string, unknown>;
  timestamp: string;
  created_at: string;
};

export type Artifact = {
  id: string;
  workspace_id: string;
  run_id: string;
  name: string;
  kind: string;
  storage_uri: string | null;
  size_bytes: number | null;
  content_type: string | null;
  hash: string | null;
  status: string;
  meta: Record<string, unknown>;
  created_at: string;
  completed_at: string | null;
};

export type ArtifactDownloadReference = {
  artifact_id: string;
  storage_uri: string | null;
  download_url: string;
};

export type RunStatusCounters = {
  created: number;
  running: number;
  finished: number;
  failed: number;
};

export type WorkspaceOverviewCounters = {
  projects_count: number;
  runs_count: number;
  run_statuses: RunStatusCounters;
  metrics_count: number;
  events_count: number;
  artifacts_count: number;
  storage_bytes: number;
};

export type ProjectOverviewCounters = {
  runs_count: number;
  run_statuses: RunStatusCounters;
  metrics_count: number;
  events_count: number;
  artifacts_count: number;
  storage_bytes: number;
};

export type WorkspaceOverview = {
  workspace: Workspace;
  counters: WorkspaceOverviewCounters;
  projects: Project[];
  recent_runs: Run[];
};

export type ProjectOverview = {
  project: Project;
  counters: ProjectOverviewCounters;
  recent_runs: Run[];
};

export type RunDetails = {
  run: Run;
  metrics: Metric[];
  events: Event[];
  artifacts: Artifact[];
};

export type CurrentApiUser = {
  user_id: string;
  workspace_id: string;
  token_id: string;
  scopes: string[];
};

export type ApiToken = {
  id: string;
  workspace_id: string;
  user_id: string;
  name: string;
  token_prefix: string;
  scopes: string[];
  expires_at: string | null;
  revoked_at: string | null;
  last_used_at: string | null;
  created_at: string;
};

export type ApiTokenCreatePayload = {
  name: string;
  user_id: string;
  scopes: string[];
  expires_at: string | null;
};

export type ApiTokenCreated = {
  id: string;
  workspace_id: string;
  user_id: string;
  name: string;
  token: string;
  token_prefix: string;
  scopes: string[];
  expires_at: string | null;
  created_at: string;
};