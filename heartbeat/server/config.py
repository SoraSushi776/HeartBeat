"""Server settings and secret loading."""
from __future__ import annotations

import json
import logging
import os
import secrets
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

API_KEY_ENV = "HEARTBEAT_API_KEY"
SECRETS_FILE_NAME = "secrets.json"
DEFAULT_DATA_DIR = Path("data")

_settings_cache: Settings | None = None


class Settings(BaseSettings):
    """Runtime settings loaded from env and optional secrets file."""

    model_config = SettingsConfigDict(env_prefix="HEARTBEAT_", extra="ignore")

    api_key: str = ""
    data_dir: Path = DEFAULT_DATA_DIR
    database_url: str = ""
    heartbeat_retention_days: int = 90
    screenshot_retention_days: int = 7
    online_timeout_ms: int = 90_000
    github_login: str = ""
    cors_origins: list[str] = Field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 8000
    default_client_id: str = ""
    screenshot_max_bytes: int = 512 * 1024
    screenshot_upload_ttl_s: int = 60

    def resolved_database_url(self) -> str:
        """Return configured database URL or default file under data_dir."""
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.data_dir / 'heartbeat.db'}"

    def snapshots_dir(self) -> Path:
        """Return the screenshot directory under data_dir."""
        return self.data_dir / "snapshots"

    def secrets_path(self) -> Path:
        """Return the local secrets file path."""
        return self.data_dir / SECRETS_FILE_NAME


def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = load_settings()
    return _settings_cache


def reset_settings() -> None:
    """Drop the cached settings so the next load re-reads sources."""
    global _settings_cache
    _settings_cache = None


def load_settings() -> Settings:
    """Build settings from env vars then data secrets file."""
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.api_key = _resolve_api_key(settings)
    return settings


def _resolve_api_key(settings: Settings) -> str:
    """Read API key from env, then secrets file, else generate and persist one."""
    env_key = os.environ.get(API_KEY_ENV, "")
    if env_key:
        return env_key
    path = settings.secrets_path()
    stored = _read_secrets_file(path)
    if stored:
        return stored
    generated = secrets.token_urlsafe(32)
    _write_secrets_file(path, generated)
    logger.info("API key generated and stored at %s", path)
    return generated


def _read_secrets_file(path: Path) -> str:
    """Return api_key from secrets file or empty string."""
    if not path.is_file():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Secrets file unreadable: %s", path)
        return ""
    value = payload.get("api_key", "")
    return value if isinstance(value, str) else ""


def _write_secrets_file(path: Path, api_key: str) -> None:
    """Persist api_key into secrets file."""
    path.write_text(json.dumps({"api_key": api_key}, indent=2) + "\n", encoding="utf-8")
