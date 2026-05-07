import { API_BASE_URL } from "./config";
import type {
  ApiToken,
  ApiTokenCreatePayload,
  ApiTokenCreated,
  Artifact,
  ArtifactDownloadReference,
  CurrentApiUser,
  Project,
  ProjectCreatePayload,
  ProjectOverview,
  RunDetails,
  WorkspaceOverview
} from "./types";

type RequestOptions = {
  method?: string;
  body?: unknown;
};

export class SaltCloudApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SaltCloudApiError";
  }
}

export class SaltCloudApi {
  private token: string;

  constructor(token: string) {
    this.token = token.trim();
  }

  async getCurrentUser(): Promise<CurrentApiUser> {
    return this.request<CurrentApiUser>("/auth/me");
  }

  async getOverview(): Promise<WorkspaceOverview> {
    return this.request<WorkspaceOverview>("/overview?recent_runs_limit=50");
  }

  async createProject(workspaceId: string, payload: ProjectCreatePayload): Promise<Project> {
    return this.request<Project>(
      `/workspaces/${encodeURIComponent(workspaceId)}/projects`,
      {
        method: "POST",
        body: payload
      }
    );
  }

  async getProjectOverview(projectId: string): Promise<ProjectOverview> {
    return this.request<ProjectOverview>(`/projects/${encodeURIComponent(projectId)}/overview?recent_runs_limit=50`);
  }

  async getRunDetails(runId: string): Promise<RunDetails> {
    return this.request<RunDetails>(`/runs/${encodeURIComponent(runId)}/details`);
  }

  async getArtifact(artifactId: string): Promise<Artifact> {
    return this.request<Artifact>(`/artifacts/${encodeURIComponent(artifactId)}`);
  }

  async getArtifactDownloadReference(artifactId: string): Promise<ArtifactDownloadReference> {
    return this.request<ArtifactDownloadReference>(`/artifacts/${encodeURIComponent(artifactId)}/download`);
  }

  async downloadArtifactContent(artifactId: string): Promise<Blob> {
    return this.requestBlob(`/artifacts/${encodeURIComponent(artifactId)}/content`);
  }

  async listApiTokens(workspaceId: string): Promise<ApiToken[]> {
    return this.request<ApiToken[]>(`/workspaces/${encodeURIComponent(workspaceId)}/api-tokens`);
  }

  async createApiToken(workspaceId: string, payload: ApiTokenCreatePayload): Promise<ApiTokenCreated> {
    return this.request<ApiTokenCreated>(
      `/workspaces/${encodeURIComponent(workspaceId)}/api-tokens`,
      {
        method: "POST",
        body: payload
      }
    );
  }

  async revokeApiToken(tokenId: string): Promise<ApiToken> {
    return this.request<ApiToken>(
      `/api-tokens/${encodeURIComponent(tokenId)}`,
      {
        method: "DELETE"
      }
    );
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    if (!this.token) {
      throw new SaltCloudApiError("API token is required");
    }

    const headers: Record<string, string> = {
      Accept: "application/json",
      Authorization: `Bearer ${this.token}`
    };

    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });

    if (!response.ok) {
      throw new SaltCloudApiError(await this.readError(response));
    }

    return response.json() as Promise<T>;
  }

  private async requestBlob(path: string): Promise<Blob> {
    if (!this.token) {
      throw new SaltCloudApiError("API token is required");
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: {
        Accept: "*/*",
        Authorization: `Bearer ${this.token}`
      }
    });

    if (!response.ok) {
      throw new SaltCloudApiError(await this.readError(response));
    }

    return response.blob();
  }

  private async readError(response: Response): Promise<string> {
    try {
      const payload = await response.json();
      const detail = payload?.detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (Array.isArray(detail)) {
        return detail.map((item) => item?.msg || String(item)).join("; ");
      }
    } catch {
      return `SaltAI Cloud error: HTTP ${response.status}`;
    }

    return `SaltAI Cloud error: HTTP ${response.status}`;
  }
}