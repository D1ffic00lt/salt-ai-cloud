export type Run = {
  id: string;
  workspace_id: string;
  project_id: string;
  created_by_id: string;
  name: string;
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

export type RunDetails = {
  run: Run;
  metrics: Metric[];
  events: Event[];
  artifacts: Artifact[];
};