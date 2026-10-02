"""Server settings and secret loading."""
from __future__ import annotations

import json
import logging
import os
import secrets
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

API_KEY_ENV = "HEARTBEAT_API_KEY"
GITHUB_TOKEN_ENV = "HEARTBEAT_GITHUB_TOKEN"
GITHUB_LOGIN_ENV = "HEARTBEAT_GITHUB_LOGIN"
SECRETS_FILE_NAME = "secrets.json"
DEFAULT_DATA_DIR = Path("data")
DEFAULT_SITE_TITLE = "HeartBeat"
DEFAULT_SITE_TAGLINE = "个人主页与实时状态"
DEFAULT_SITE_PROCESS_TITLE = "TA的电脑上正在玩"
DEFAULT_SITE_TAGS_TITLE = "标签"
DEFAULT_SITE_ICP_TEXT = "萌ICP备20263011号"
DEFAULT_SITE_ICP_KEYWORD = "20263011"
DEFAULT_GITHUB_OWNER = "SoraSushi776"
DEFAULT_GITHUB_REPO = "HeartBeat"

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
    github_token: str = ""
    cors_origins: list[str] = Field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 8000
    default_client_id: str = ""
    screenshot_max_bytes: int = 512 * 1024
    screenshot_upload_ttl_s: int = 60
    docs_enabled: bool = False

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
    stored = _read_secrets_payload(settings.secrets_path())
    settings.api_key = _resolve_api_key(settings, stored)
    settings.github_token = _resolve_secret(GITHUB_TOKEN_ENV, "github_token", stored)
    stored_login = _resolve_secret(GITHUB_LOGIN_ENV, "github_login", stored)
    settings.github_login = stored_login or settings.github_login
    return settings


def save_github_token(token: str, login: str | None = None) -> None:
    """Persist the GitHub PAT and optional login into the secrets file."""
    settings = get_settings()
    payload = _read_secrets_payload(settings.secrets_path())
    payload["github_token"] = token
    if login:
        payload["github_login"] = login
        settings.github_login = login
    _write_secrets_payload(settings.secrets_path(), payload)
    settings.github_token = token
    logger.info("GitHub token stored in secrets file")


def load_site_settings() -> dict[str, Any]:
    """Return the stored site copy or protocol defaults when unset."""
    stored = _read_secrets_payload(get_settings().secrets_path()).get("site")
    data = stored if isinstance(stored, dict) else {}
    tags_raw = data.get("tags")
    tags = [str(item).strip() for item in tags_raw] if isinstance(tags_raw, list) else []
    show_raw = data.get("show_heatmap")
    show_heatmap = show_raw if isinstance(show_raw, bool) else True
    show_icp_raw = data.get("show_icp")
    show_icp = show_icp_raw if isinstance(show_icp_raw, bool) else False
    return {
        "title": _site_value(data, "title", DEFAULT_SITE_TITLE),
        "tagline": _site_value(data, "tagline", DEFAULT_SITE_TAGLINE),
        "process_title": _site_value(data, "process_title", DEFAULT_SITE_PROCESS_TITLE),
        "show_heatmap": show_heatmap,
        "tags_title": _site_value(data, "tags_title", DEFAULT_SITE_TAGS_TITLE),
        "tags": [item for item in tags if item],
        "show_icp": show_icp,
        "icp_text": _site_value(data, "icp_text", DEFAULT_SITE_ICP_TEXT),
        "icp_keyword": _site_value(data, "icp_keyword", DEFAULT_SITE_ICP_KEYWORD),
        "github_owner": _site_value(data, "github_owner", DEFAULT_GITHUB_OWNER),
        "github_repo": _site_value(data, "github_repo", DEFAULT_GITHUB_REPO),
    }


def save_site_settings(values: dict[str, Any]) -> dict[str, Any]:
    """Merge the given site copy fields into the secrets file and return the result."""
    settings = get_settings()
    payload = _read_secrets_payload(settings.secrets_path())
    stored = payload.get("site")
    data = dict(stored) if isinstance(stored, dict) else {}
    for key, value in values.items():
        data[key] = value
    payload["site"] = data
    _write_secrets_payload(settings.secrets_path(), payload)
    logger.info("Site settings stored in secrets file")
    return load_site_settings()


def _site_value(data: dict[str, Any], key: str, default: str) -> str:
    """Return a string field from the site object, or the default when absent."""
    value = data.get(key)
    if isinstance(value, str):
        return value.strip()
    return default


def _resolve_secret(env_name: str, secrets_key: str, stored: dict[str, Any]) -> str:
    """Read a secret from env first, then the secrets file."""
    env_value = os.environ.get(env_name, "")
    if env_value:
        return env_value
    value = stored.get(secrets_key, "")
    return value if isinstance(value, str) else ""


def _resolve_api_key(settings: Settings, stored: dict[str, Any]) -> str:
    """Read API key from env, then secrets file, else generate and persist one."""
    env_key = os.environ.get(API_KEY_ENV, "")
    if env_key:
        return env_key
    existing = stored.get("api_key", "")
    if isinstance(existing, str) and existing:
        return existing
    generated = secrets.token_urlsafe(32)
    _write_secrets_payload(settings.secrets_path(), {**stored, "api_key": generated})
    logger.info("API key generated and stored at %s", settings.secrets_path())
    return generated


def _read_secrets_payload(path: Path) -> dict[str, Any]:
    """Return the secrets file object or an empty dict when unreadable."""
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Secrets file unreadable: %s", path)
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_secrets_payload(path: Path, payload: dict[str, Any]) -> None:
    """Persist the secrets object to disk."""
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
