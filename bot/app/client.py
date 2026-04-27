from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class SaltCloudClientError(RuntimeError):
    pass


class SaltCloudClient:
    def __init__(
            self,
            base_url: str,
            api_prefix: str = "/api/v1",
            api_token: str | None = None,
            timeout: int = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/" + api_prefix.strip("/")
        self.api_token = api_token
        self.timeout = timeout

    @property
    def is_authenticated(self) -> bool:
        return self.api_token is not None and bool(self.api_token.strip())

    def list_project_runs(self, project_id: str) -> list[dict[str, Any]]:
        data = self._request("GET", f"/projects/{quote(project_id)}/runs")
        if not isinstance(data, list):
            raise SaltCloudClientError("Unexpected runs response")
        return data

    def get_run(self, run_id: str) -> dict[str, Any]:
        data = self._request("GET", f"/runs/{quote(run_id)}")
        if not isinstance(data, dict):
            raise SaltCloudClientError("Unexpected run response")
        return data

    def get_run_details(self, run_id: str) -> dict[str, Any]:
        data = self._request("GET", f"/runs/{quote(run_id)}/details")
        if not isinstance(data, dict):
            raise SaltCloudClientError("Unexpected run details response")
        return data

    def list_run_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        data = self._request("GET", f"/runs/{quote(run_id)}/artifacts")
        if not isinstance(data, list):
            raise SaltCloudClientError("Unexpected artifacts response")
        return data

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        data = self._request("GET", f"/artifacts/{quote(artifact_id)}")
        if not isinstance(data, dict):
            raise SaltCloudClientError("Unexpected artifact response")
        return data

    def _request(
            self,
            method: str,
            path: str,
            payload: dict[str, Any] | None = None,
    ) -> Any:
        url = self._url(path)
        body = None
        headers = {
            "Accept": "application/json",
        }

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        request = Request(
            url=url,
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = self._read_error(exc)
            raise SaltCloudClientError(detail) from exc
        except URLError as exc:
            raise SaltCloudClientError(f"Cannot reach SaltAI Cloud: {exc.reason}") from exc
        except TimeoutError as exc:
            raise SaltCloudClientError("SaltAI Cloud request timed out") from exc

        if not raw:
            return None

        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SaltCloudClientError("SaltAI Cloud returned invalid JSON") from exc

    def _url(self, path: str) -> str:
        return f"{self.base_url}{self.api_prefix}/{path.lstrip('/')}"

    @staticmethod
    def _read_error(exc: HTTPError) -> str:
        raw = exc.read()

        if not raw:
            return f"SaltAI Cloud error: HTTP {exc.code}"

        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return f"SaltAI Cloud error: HTTP {exc.code}"

        detail = data.get("detail")
        if isinstance(detail, str):
            return detail

        return f"SaltAI Cloud error: HTTP {exc.code}"
