from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Protocol

from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.paths import ensure_config_dir

logger = logging.getLogger(__name__)


class SecretStore(Protocol):
    """Api key storage backend."""

    def load_api_key(self) -> str:
        """Return the stored api_key or empty string."""

    def save_api_key(self, value: str) -> None:
        """Persist the api_key."""


class ConfigStore:
    """Load and persist the main client.json configuration."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppConfig:
        """Read client.json and fall back to defaults on bad data."""
        raw = self._read_json()
        config = AppConfig.from_dict(raw)
        if not config.client_id:
            config.client_id = uuid.uuid4().hex[:12]
            self.save(config)
        return config

    def save(self, config: AppConfig) -> None:
        """Write client.json, creating the parent directory when needed."""
        ensure_config_dir()
        payload = config.to_dict()
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Client config saved: %s", self._path)

    def _read_json(self) -> dict[str, Any]:
        if not self._path.exists():
            logger.info("Client config missing, using defaults: %s", self._path)
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Client config unreadable, using defaults")
            return {}
        return data if isinstance(data, dict) else {}


class JsonSecretStore:
    """Persist api_key in client.secrets.json with restricted permissions."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load_api_key(self) -> str:
        """Return the stored api_key or an empty string."""
        data = self._read_json()
        value = data.get("api_key")
        return value if isinstance(value, str) else ""

    def save_api_key(self, value: str) -> None:
        """Write api_key to secrets file and chmod 0600."""
        ensure_config_dir()
        self._path.write_text(json.dumps({"api_key": value}, ensure_ascii=False), encoding="utf-8")
        os.chmod(self._path, 0o600)
        logger.info("Api key saved: %s", self._path)

    def _read_json(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Secrets file unreadable")
            return {}
        return data if isinstance(data, dict) else {}
