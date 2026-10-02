"""Public exposure policy for files served under the static prefix."""
from __future__ import annotations

import logging
from pathlib import PurePosixPath
from urllib.parse import unquote

from heartbeat.server.config import Settings, get_settings

logger = logging.getLogger(__name__)

STATIC_PREFIX = "/static"
PUBLIC_DIR_NAMES: frozenset[str] = frozenset({"backgrounds", "covers", "snapshots"})
PUBLIC_SUFFIXES: frozenset[str] = frozenset(
    {".avif", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
)
BLOCKED_NAMES: frozenset[str] = frozenset(
    {"heartbeat.db", "heartbeat.db-shm", "heartbeat.db-wal", "secrets.json"}
)


class StaticAccessPolicy:
    """Decide which files under the static prefix may be served publicly."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Bind the policy to settings, falling back to the process singleton."""
        self._settings = settings or get_settings()

    def public_mounts(self) -> dict[str, str]:
        """Return mount path to directory pairs that are publicly readable."""
        return {
            f"{STATIC_PREFIX}/{name}": str(self._settings.data_dir / name)
            for name in sorted(PUBLIC_DIR_NAMES)
        }

    def applies(self, path: str) -> bool:
        """Return True when the request path targets the static prefix."""
        return path.startswith(f"{STATIC_PREFIX}/")

    def allows(self, path: str) -> bool:
        """Return True when the path points at a public image asset."""
        parts = _static_parts(path)
        if parts is None:
            return False
        if not parts or parts[0] not in PUBLIC_DIR_NAMES:
            return False
        if any(part in {"..", ""} for part in parts):
            return False
        name = parts[-1]
        if name in BLOCKED_NAMES or name.startswith("."):
            return False
        return PurePosixPath(name).suffix.lower() in PUBLIC_SUFFIXES


def _static_parts(path: str) -> tuple[str, ...] | None:
    """Return decoded path segments below the static prefix, or None when unrelated."""
    if not path.startswith(f"{STATIC_PREFIX}/"):
        return None
    relative = unquote(path[len(STATIC_PREFIX) + 1 :])
    return PurePosixPath(relative).parts
