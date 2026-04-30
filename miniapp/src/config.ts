export const API_BASE_URL = (
  import.meta.env.VITE_SALTAI_CLOUD_API_BASE_URL || "/api/v1"
).replace(/\/$/, "");

export const TOKEN_STORAGE_KEY = "saltai_cloud_api_token";
export const PROJECT_STORAGE_KEY = "saltai_cloud_project_id";