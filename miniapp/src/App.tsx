import { useEffect, useMemo, useState } from "react";

import { SaltCloudApi, SaltCloudApiError } from "./api";
import { TOKEN_STORAGE_KEY } from "./config";
import type {
  ApiToken,
  ApiTokenCreated,
  Artifact,
  CurrentApiUser,
  Project,
  Run,
  RunDetails,
  WorkspaceOverview
} from "./types";

type View = "dashboard" | "settings";
type TokenPreset = "read" | "write" | "full";

const TOKEN_PRESETS: Record<TokenPreset, { label: string; scopes: string[] }> = {
  read: {
    label: "Read-only",
    scopes: [
      "workspaces:read",
      "projects:read",
      "runs:read",
      "metrics:read",
      "events:read",
      "artifacts:read"
    ]
  },
  write: {
    label: "Logger write",
    scopes: [
      "workspaces:read",
      "projects:read",
      "runs:read",
      "runs:write",
      "metrics:read",
      "metrics:write",
      "events:read",
      "events:write",
      "artifacts:read",
      "artifacts:write"
    ]
  },
  full: {
    label: "Full workspace",
    scopes: ["*"]
  }
};

export function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) || "");
  const [view, setView] = useState<View>("dashboard");
  const [overview, setOverview] = useState<WorkspaceOverview | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentApiUser | null>(null);
  const [apiTokens, setApiTokens] = useState<ApiToken[]>([]);
  const [createdToken, setCreatedToken] = useState<ApiTokenCreated | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunDetails, setSelectedRunDetails] = useState<RunDetails | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [newTokenName, setNewTokenName] = useState("Mini App read-only");
  const [newTokenPreset, setNewTokenPreset] = useState<TokenPreset>("read");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const api = useMemo(() => new SaltCloudApi(token), [token]);

  useEffect(() => {
    const telegram = window.Telegram?.WebApp;

    telegram?.ready();
    telegram?.expand();
  }, []);

  function saveToken(value: string) {
    setToken(value);

    if (value.trim()) {
      localStorage.setItem(TOKEN_STORAGE_KEY, value);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }

    setCurrentUser(null);
    setApiTokens([]);
    setCreatedToken(null);
  }

  async function loadOverview() {
    await runAction(async () => {
      const user = await api.getCurrentUser();
      const data = await api.getOverview();

      data.projects = sortByDate(data.projects, "created_at");
      data.recent_runs = sortByDate(data.recent_runs, "created_at");

      setCurrentUser(user);
      setOverview(data);
      setSelectedProject(null);
      setRuns(data.recent_runs);
      setSelectedRunDetails(null);
      setSelectedArtifact(null);
    });
  }

  async function loadSettings() {
    await runAction(async () => {
      const user = await api.getCurrentUser();
      const tokens = await api.listApiTokens(user.workspace_id);

      setCurrentUser(user);
      setApiTokens(sortByDate(tokens, "created_at"));
    });
  }

  async function createApiToken() {
    await runAction(async () => {
      const user = currentUser || await api.getCurrentUser();
      const preset = TOKEN_PRESETS[newTokenPreset];

      const created = await api.createApiToken(user.workspace_id, {
        name: newTokenName.trim() || preset.label,
        user_id: user.user_id,
        scopes: preset.scopes,
        expires_at: null
      });

      const tokens = await api.listApiTokens(user.workspace_id);

      setCurrentUser(user);
      setCreatedToken(created);
      setApiTokens(sortByDate(tokens, "created_at"));
    });
  }

  async function revokeApiToken(tokenId: string) {
    await runAction(async () => {
      const user = currentUser || await api.getCurrentUser();

      await api.revokeApiToken(tokenId);

      const tokens = await api.listApiTokens(user.workspace_id);

      setCurrentUser(user);
      setApiTokens(sortByDate(tokens, "created_at"));
    });
  }

  async function openProject(project: Project) {
    await runAction(async () => {
      const data = await api.getProjectOverview(project.id);

      data.recent_runs = sortByDate(data.recent_runs, "created_at");

      setSelectedProject(data.project);
      setRuns(data.recent_runs);
      setSelectedRunDetails(null);
      setSelectedArtifact(null);
    });
  }

  async function openRun(runId: string) {
    await runAction(async () => {
      const data = await api.getRunDetails(runId);

      data.metrics = sortByDate(data.metrics, "timestamp");
      data.events = sortByDate(data.events, "timestamp");
      data.artifacts = sortByDate(data.artifacts, "created_at");

      setSelectedRunDetails(data);
      setSelectedArtifact(null);
    });
  }

  async function openArtifact(artifactId: string) {
    await runAction(async () => {
      const data = await api.getArtifact(artifactId);

      setSelectedArtifact(data);
    });
  }

  async function runAction(action: () => Promise<void>) {
    setLoading(true);
    setError("");

    try {
      await action();
    } catch (err) {
      if (err instanceof SaltCloudApiError) {
        setError(err.message);
      } else {
        setError("Unexpected Mini App error");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero card">
        <div>
          <p className="eyebrow">SaltAI Cloud</p>
          <h1>Mini App</h1>
          <p className="muted">Dashboard для просмотра runs и settings для управления API tokens.</p>
        </div>

        <div className="tabs">
          <button
            className={view === "dashboard" ? "tab active" : "tab"}
            onClick={() => setView("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={view === "settings" ? "tab active" : "tab"}
            onClick={() => setView("settings")}
          >
            Settings
          </button>
        </div>
      </section>

      <section className="card form-card">
        <label>
          <span>API token</span>
          <input
            type="password"
            value={token}
            placeholder="saltai_..."
            onChange={(event) => saveToken(event.target.value)}
          />
        </label>

        <button disabled={loading} onClick={view === "settings" ? loadSettings : loadOverview}>
          {loading ? "Loading..." : view === "settings" ? "Load Settings" : "Load SaltAI Cloud"}
        </button>

        {currentUser && (
          <div className="token-chip">
            <span>workspace</span>
            <code>{currentUser.workspace_id}</code>
          </div>
        )}

        {error && <p className="error">{error}</p>}
      </section>

      {view === "dashboard" ? (
        <DashboardView
          overview={overview}
          selectedProject={selectedProject}
          runs={runs}
          selectedRunDetails={selectedRunDetails}
          selectedArtifact={selectedArtifact}
          onOpenProject={openProject}
          onOpenRun={openRun}
          onOpenArtifact={openArtifact}
        />
      ) : (
        <SettingsView
          currentUser={currentUser}
          apiTokens={apiTokens}
          createdToken={createdToken}
          newTokenName={newTokenName}
          newTokenPreset={newTokenPreset}
          loading={loading}
          onLoadSettings={loadSettings}
          onCreateToken={createApiToken}
          onRevokeToken={revokeApiToken}
          onNewTokenNameChange={setNewTokenName}
          onNewTokenPresetChange={setNewTokenPreset}
        />
      )}
    </main>
  );
}

function DashboardView({
  overview,
  selectedProject,
  runs,
  selectedRunDetails,
  selectedArtifact,
  onOpenProject,
  onOpenRun,
  onOpenArtifact
}: {
  overview: WorkspaceOverview | null;
  selectedProject: Project | null;
  runs: Run[];
  selectedRunDetails: RunDetails | null;
  selectedArtifact: Artifact | null;
  onOpenProject: (project: Project) => void;
  onOpenRun: (runId: string) => void;
  onOpenArtifact: (artifactId: string) => void;
}) {
  return (
    <>
      {overview && (
        <section className="card hero">
          <div className="section-header">
            <h2>{overview.workspace.name}</h2>
            <span>{overview.workspace.slug}</span>
          </div>

          <div className="stats">
            <Stat label="projects" value={overview.counters.projects_count} />
            <Stat label="runs" value={overview.counters.runs_count} />
            <Stat label="artifacts" value={overview.counters.artifacts_count} />
          </div>
        </section>
      )}

      <section className="grid">
        <div className="card">
          <div className="section-header">
            <h2>Projects</h2>
            <span>{overview?.projects.length || 0}</span>
          </div>

          {overview ? (
            <ProjectsView
              projects={overview.projects}
              selectedProjectId={selectedProject?.id || ""}
              onOpenProject={onOpenProject}
            />
          ) : (
            <p className="muted">Введи token и нажми Load SaltAI Cloud.</p>
          )}
        </div>

        <div className="card">
          <div className="section-header">
            <h2>{selectedProject ? "Project runs" : "Recent runs"}</h2>
            <span>{runs.length}</span>
          </div>

          <RunsView
            project={selectedProject}
            runs={runs}
            onOpenRun={onOpenRun}
          />
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <div className="section-header">
            <h2>Run details</h2>
            {selectedRunDetails && <span>{selectedRunDetails.run.status}</span>}
          </div>

          {selectedRunDetails ? (
            <RunDetailsView
              details={selectedRunDetails}
              onOpenArtifact={onOpenArtifact}
            />
          ) : (
            <p className="muted">Выбери run из списка.</p>
          )}
        </div>

        <div className="card">
          <div className="section-header">
            <h2>Artifact details</h2>
            {selectedArtifact && <span>{selectedArtifact.status}</span>}
          </div>

          {selectedArtifact ? (
            <ArtifactView artifact={selectedArtifact} />
          ) : (
            <p className="muted">Выбери artifact внутри run details.</p>
          )}
        </div>
      </section>
    </>
  );
}

function SettingsView({
  currentUser,
  apiTokens,
  createdToken,
  newTokenName,
  newTokenPreset,
  loading,
  onLoadSettings,
  onCreateToken,
  onRevokeToken,
  onNewTokenNameChange,
  onNewTokenPresetChange
}: {
  currentUser: CurrentApiUser | null;
  apiTokens: ApiToken[];
  createdToken: ApiTokenCreated | null;
  newTokenName: string;
  newTokenPreset: TokenPreset;
  loading: boolean;
  onLoadSettings: () => void;
  onCreateToken: () => void;
  onRevokeToken: (tokenId: string) => void;
  onNewTokenNameChange: (value: string) => void;
  onNewTokenPresetChange: (value: TokenPreset) => void;
}) {
  return (
    <section className="grid settings-grid">
      <div className="card">
        <div className="section-header">
          <h2>Current token</h2>
          {currentUser && <span>{currentUser.scopes.includes("*") ? "full" : `${currentUser.scopes.length} scopes`}</span>}
        </div>

        {currentUser ? (
          <div className="details">
            <KeyValue label="user" value={currentUser.user_id} />
            <KeyValue label="workspace" value={currentUser.workspace_id} />
            <KeyValue label="token" value={currentUser.token_id} />

            <h4>Scopes</h4>
            <ScopesView scopes={currentUser.scopes} />
          </div>
        ) : (
          <div className="details">
            <p className="muted">Нажми Load Settings, чтобы подтянуть текущий token и workspace.</p>
            <button disabled={loading} onClick={onLoadSettings}>
              Load Settings
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="section-header">
          <h2>Create API token</h2>
          <span>{TOKEN_PRESETS[newTokenPreset].label}</span>
        </div>

        <div className="details">
          <label>
            <span>Token name</span>
            <input
              value={newTokenName}
              placeholder="Mini App read-only"
              onChange={(event) => onNewTokenNameChange(event.target.value)}
            />
          </label>

          <label>
            <span>Preset</span>
            <select
              value={newTokenPreset}
              onChange={(event) => onNewTokenPresetChange(event.target.value as TokenPreset)}
            >
              <option value="read">Read-only</option>
              <option value="write">Logger write</option>
              <option value="full">Full workspace</option>
            </select>
          </label>

          <ScopesView scopes={TOKEN_PRESETS[newTokenPreset].scopes} />

          <button disabled={loading || !currentUser} onClick={onCreateToken}>
            Create token
          </button>

          {createdToken && (
            <div className="created-token">
              <p className="muted">Сохрани token сейчас: потом backend его больше не покажет.</p>
              <code>{createdToken.token}</code>
            </div>
          )}
        </div>
      </div>

      <div className="card wide-card">
        <div className="section-header">
          <h2>Workspace API tokens</h2>
          <span>{apiTokens.length}</span>
        </div>

        {apiTokens.length === 0 ? (
          <p className="muted">Tokens не загружены или у текущего token нет права tokens:write.</p>
        ) : (
          <div className="list">
            {apiTokens.map((apiToken) => (
              <div className="list-item token-row" key={apiToken.id}>
                <span className="item-title">
                  {apiToken.name}
                  {apiToken.id === currentUser?.token_id ? " · current" : ""}
                  {apiToken.revoked_at ? " · revoked" : ""}
                </span>
                <span className="item-meta">{apiToken.token_prefix}...</span>
                <span className="item-id">{apiToken.id}</span>

                <div className="token-row-footer">
                  <span>{apiToken.scopes.includes("*") ? "*" : apiToken.scopes.join(", ")}</span>
                  <button
                    disabled={loading || Boolean(apiToken.revoked_at)}
                    onClick={() => onRevokeToken(apiToken.id)}
                  >
                    Revoke
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function ProjectsView({
  projects,
  selectedProjectId,
  onOpenProject
}: {
  projects: Project[];
  selectedProjectId: string;
  onOpenProject: (project: Project) => void;
}) {
  if (projects.length === 0) {
    return <p className="muted">Projects пока нет.</p>;
  }

  return (
    <div className="list">
      {projects.map((project) => (
        <button
          key={project.id}
          className="list-item"
          onClick={() => onOpenProject(project)}
        >
          <span className="item-title">
            {project.name || "unnamed"}
            {project.id === selectedProjectId ? " · selected" : ""}
          </span>
          <span className="item-meta">{project.description || "no description"}</span>
          <span className="item-id">{project.id}</span>
        </button>
      ))}
    </div>
  );
}

function RunsView({
  project,
  runs,
  onOpenRun
}: {
  project: Project | null;
  runs: Run[];
  onOpenRun: (runId: string) => void;
}) {
  if (runs.length === 0) {
    return (
      <div className="details">
        {project && <KeyValue label="project" value={project.id} />}
        <p className="muted">Runs пока нет.</p>
      </div>
    );
  }

  return (
    <div className="details">
      {project && <KeyValue label="project" value={project.id} />}

      <div className="list">
        {runs.map((run) => (
          <button
            key={run.id}
            className="list-item"
            onClick={() => onOpenRun(run.id)}
          >
            <span className="item-title">{run.name || "unnamed"}</span>
            <span className="item-meta">{run.status}</span>
            <span className="item-id">{run.id}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function RunDetailsView({
  details,
  onOpenArtifact
}: {
  details: RunDetails;
  onOpenArtifact: (artifactId: string) => void;
}) {
  const run = details.run;

  return (
    <div className="details">
      <h3>{run.name || "unnamed"}</h3>
      <KeyValue label="id" value={run.id} />
      <KeyValue label="project" value={run.project_id} />
      <KeyValue label="created" value={formatDate(run.created_at)} />
      <KeyValue label="started" value={formatDate(run.started_at)} />
      <KeyValue label="finished" value={formatDate(run.finished_at)} />

      <div className="stats">
        <Stat label="metrics" value={details.metrics.length} />
        <Stat label="events" value={details.events.length} />
        <Stat label="artifacts" value={details.artifacts.length} />
      </div>

      <h4>Latest metrics</h4>
      {details.metrics.length === 0 ? (
        <p className="muted">No metrics.</p>
      ) : (
        details.metrics.slice(0, 5).map((metric) => (
          <div className="compact-row" key={metric.id}>
            <span>{metric.key}</span>
            <code>{metric.value}</code>
          </div>
        ))
      )}

      <h4>Latest events</h4>
      {details.events.length === 0 ? (
        <p className="muted">No events.</p>
      ) : (
        details.events.slice(0, 5).map((event) => (
          <div className="compact-row" key={event.id}>
            <span>{event.type}</span>
            <code>{event.level}</code>
          </div>
        ))
      )}

      <h4>Artifacts</h4>
      {details.artifacts.length === 0 ? (
        <p className="muted">No artifacts.</p>
      ) : (
        <div className="list">
          {details.artifacts.slice(0, 10).map((artifact) => (
            <button
              key={artifact.id}
              className="list-item"
              onClick={() => onOpenArtifact(artifact.id)}
            >
              <span className="item-title">{artifact.name || "unnamed"}</span>
              <span className="item-meta">{artifact.kind}</span>
              <span className="item-id">{artifact.id}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ArtifactView({ artifact }: { artifact: Artifact }) {
  return (
    <div className="details">
      <h3>{artifact.name || "unnamed"}</h3>
      <KeyValue label="id" value={artifact.id} />
      <KeyValue label="run" value={artifact.run_id} />
      <KeyValue label="kind" value={artifact.kind} />
      <KeyValue label="status" value={artifact.status} />
      <KeyValue label="size" value={formatSize(artifact.size_bytes)} />
      <KeyValue label="content type" value={artifact.content_type || ""} />
      <KeyValue label="hash" value={artifact.hash || ""} />
      <KeyValue label="created" value={formatDate(artifact.created_at)} />
      <KeyValue label="completed" value={formatDate(artifact.completed_at)} />
      <KeyValue label="storage" value={artifact.storage_uri || ""} />

      {Object.keys(artifact.meta || {}).length > 0 && (
        <>
          <h4>Meta</h4>
          {Object.entries(artifact.meta).map(([key, value]) => (
            <div className="compact-row" key={key}>
              <span>{key}</span>
              <code>{String(value)}</code>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function ScopesView({ scopes }: { scopes: string[] }) {
  return (
    <div className="scopes">
      {scopes.map((scope) => (
        <code key={scope}>{scope}</code>
      ))}
    </div>
  );
}

function KeyValue({ label, value }: { label: string; value: string }) {
  if (!value) {
    return null;
  }

  return (
    <div className="key-value">
      <span>{label}</span>
      <code>{value}</code>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function sortByDate<T extends Record<string, unknown>>(items: T[], key: keyof T): T[] {
  return [...items].sort((a, b) => {
    const left = String(a[key] || "");
    const right = String(b[key] || "");
    return right.localeCompare(left);
  });
}

function formatDate(value: string | null): string {
  if (!value) {
    return "";
  }

  return value.replace("T", " ").replace("Z", "");
}

function formatSize(value: number | null): string {
  if (value === null) {
    return "";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;

  for (const unit of units) {
    if (size < 1024 || unit === units[units.length - 1]) {
      if (unit === "B") {
        return `${Math.round(size)} ${unit}`;
      }

      return `${size.toFixed(2)} ${unit}`;
    }

    size /= 1024;
  }

  return `${value} B`;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
      };
    };
  }
}