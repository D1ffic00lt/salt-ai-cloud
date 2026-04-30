import { API_BASE_URL } from "./config";
import type { Artifact, Run, RunDetails } from "./types";

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

  async listProjectRuns(projectId: string): Promise<Run[]> {
    return this.request<Run[]>(`/projects/${encodeURIComponent(projectId)}/runs`);
  }

  async getRunDetails(runId: string): Promise<RunDetails> {
    return this.request<RunDetails>(`/runs/${encodeURIComponent(runId)}/details`);
  }

  async listRunArtifacts(runId: string): Promise<Artifact[]> {
    return this.request<Artifact[]>(`/runs/${encodeURIComponent(runId)}/artifacts`);
  }

  async getArtifact(artifactId: string): Promise<Artifact> {
    return this.request<Artifact>(`/artifacts/${encodeURIComponent(artifactId)}`);
  }

  private async request<T>(path: string): Promise<T> {
    if (!this.token) {
      throw new SaltCloudApiError("API token is required");
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${this.token}`
      }
    });

    if (!response.ok) {
      throw new SaltCloudApiError(await this.readError(response));
    }

    return response.json() as Promise<T>;
  }

  private async readError(response: Response): Promise<string> {
    try {
      const payload = await response.json();
      const detail = payload?.detail;

      if (typeof detail === "string") {
        return detail;
      }
    } catch {
      return `SaltAI Cloud error: HTTP ${response.status}`;
    }

    return `SaltAI Cloud error: HTTP ${response.status}`;
  }
}