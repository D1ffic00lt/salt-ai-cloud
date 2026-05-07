from dataclasses import dataclass
from os import getenv


def _optional_env(name: str) -> str | None:
    value = getenv(name)
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    return value


def _int_env(name: str, default: int) -> int:
    value = getenv(name)
    if value is None:
        return default

    value = value.strip()
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = getenv(name)
    if value is None:
        return default

    value = value.strip().lower()
    if not value:
        return default

    return value in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    cloud_base_url: str
    cloud_api_prefix: str
    cloud_api_token: str | None
    default_project_id: str | None
    mini_app_url: str | None
    mini_app_pass_token: bool
    polling_timeout: int
    runs_limit: int
    artifacts_limit: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            cloud_base_url=getenv("SALTAI_CLOUD_BASE_URL", "http://localhost:8000").strip(),
            cloud_api_prefix=getenv("SALTAI_CLOUD_API_PREFIX", "/api/v1").strip(),
            cloud_api_token=_optional_env("SALTAI_CLOUD_API_TOKEN"),
            default_project_id=_optional_env("SALTAI_DEFAULT_PROJECT_ID"),
            mini_app_url=_optional_env("SALTAI_MINI_APP_URL"),
            mini_app_pass_token=_bool_env("SALTAI_MINI_APP_PASS_TOKEN", True),
            polling_timeout=_int_env("SALTAI_BOT_POLLING_TIMEOUT", 20),
            runs_limit=max(1, _int_env("SALTAI_BOT_RUNS_LIMIT", 10)),
            artifacts_limit=max(1, _int_env("SALTAI_BOT_ARTIFACTS_LIMIT", 10)),
        )

    @property
    def has_cloud_token(self) -> bool:
        return self.cloud_api_token is not None

    def validate_bot(self) -> None:
        if not self.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
