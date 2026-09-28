"""Screenshot file storage under the data directory."""
from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from heartbeat.server.config import get_settings

logger = logging.getLogger(__name__)

LATEST_SUFFIX = "latest"
META_SUFFIX = "meta.json"
WEBP_SUFFIX = "webp"


@dataclass(frozen=True)
class SnapshotInfo:
    """Metadata for one stored screenshot."""

    client_id: str
    url: str
    ts: int
    width: int
    height: int
    path: Path


class SnapshotStore:
    """Persist WebP screenshots and their sidecar metadata."""

    _instance: SnapshotStore | None = None

    @classmethod
    def instance(cls) -> SnapshotStore:
        """Return the process-wide snapshot store singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def save_latest(self, client_id: str, webp: bytes, ts: int) -> SnapshotInfo:
        """Write latest WebP plus meta sidecar and a per-day history copy."""
        settings = get_settings()
        directory = settings.snapshots_dir()
        directory.mkdir(parents=True, exist_ok=True)
        width, height = probe_webp_size(webp)
        latest_path = directory / f"{client_id}-{LATEST_SUFFIX}.{WEBP_SUFFIX}"
        latest_path.write_bytes(webp)
        info = SnapshotInfo(
            client_id=client_id,
            url=public_url(client_id),
            ts=ts,
            width=width,
            height=height,
            path=latest_path,
        )
        write_meta(info)
        self._write_daily(client_id, webp, ts)
        logger.info("Screenshot stored for client=%s ts=%d", client_id, ts)
        return info

    def read_latest(self, client_id: str) -> SnapshotInfo | None:
        """Return latest snapshot metadata for a client if present."""
        settings = get_settings()
        meta_path = settings.snapshots_dir() / f"{client_id}-{LATEST_SUFFIX}.{META_SUFFIX}"
        if not meta_path.is_file():
            return None
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Snapshot meta unreadable: %s", meta_path)
            return None
        return SnapshotInfo(
            client_id=client_id,
            url=public_url(client_id),
            ts=int(payload.get("ts", 0)),
            width=int(payload.get("width", 0)),
            height=int(payload.get("height", 0)),
            path=settings.snapshots_dir() / f"{client_id}-{LATEST_SUFFIX}.{WEBP_SUFFIX}",
        )

    def daily_paths(self, client_id: str) -> list[Path]:
        """Return per-day history screenshot paths for a client."""
        directory = get_settings().snapshots_dir()
        if not directory.is_dir():
            return []
        return sorted(
            path
            for path in directory.glob(f"{client_id}-*.{WEBP_SUFFIX}")
            if LATEST_SUFFIX not in path.stem
        )

    def _write_daily(self, client_id: str, webp: bytes, ts: int) -> None:
        """Write a history copy keyed by the UTC date of ts."""
        day = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).date().isoformat()
        path = get_settings().snapshots_dir() / f"{client_id}-{day}.{WEBP_SUFFIX}"
        if not path.exists():
            path.write_bytes(webp)


def public_url(client_id: str) -> str:
    """Return the public static URL for a client's latest screenshot."""
    return f"/static/snapshots/{client_id}-{LATEST_SUFFIX}.{WEBP_SUFFIX}"


def write_meta(info: SnapshotInfo) -> None:
    """Persist snapshot metadata sidecar next to the WebP file."""
    meta_path = info.path.with_name(f"{info.client_id}-{LATEST_SUFFIX}.{META_SUFFIX}")
    payload = {
        "ts": info.ts,
        "width": info.width,
        "height": info.height,
        "url": info.url,
    }
    meta_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def probe_webp_size(webp: bytes) -> tuple[int, int]:
    """Return width and height of a WebP byte payload, zero on failure."""
    try:
        with Image.open(io.BytesIO(webp)) as image:
            return int(image.width), int(image.height)
    except Exception:
        logger.warning("WebP size probe failed, defaulting to zero")
        return 0, 0
