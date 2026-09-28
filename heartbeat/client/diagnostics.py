"""Live diagnostics snapshot model and cover decoding helpers."""

from __future__ import annotations

import base64
import binascii
import logging
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

from heartbeat.protocol.models import MediaInfo, ProcessInfo, SystemInfo

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticsSnapshot:
    """Live local collection result for the diagnostics panel."""

    media: MediaInfo | None = None
    processes: list[ProcessInfo] = field(default_factory=list)
    system: SystemInfo | None = None
    cover_bytes: bytes | None = None


def read_cover_bytes(cover_url: str | None) -> bytes | None:
    """Return raw image bytes from a data URL, file URL, or local path."""
    if not cover_url:
        return None
    if cover_url.startswith("data:"):
        return _data_url_bytes(cover_url)
    return _local_file_bytes(cover_url)


def format_ms(value: int | None) -> str:
    """Format a millisecond duration as m:ss, or a placeholder when missing."""
    if value is None or value < 0:
        return "--:--"
    total = value // 1000
    return f"{total // 60}:{total % 60:02d}"


def _data_url_bytes(url: str) -> bytes | None:
    _, _, payload = url.partition(",")
    if not payload:
        return None
    try:
        return base64.b64decode(payload)
    except (ValueError, binascii.Error):
        logger.warning("Cover data URL decode failed")
        return None


def _local_file_bytes(url: str) -> bytes | None:
    parsed = urlparse(url)
    raw = unquote(parsed.path) if parsed.scheme == "file" else url
    path = Path(raw)
    if not path.is_file():
        return None
    try:
        return path.read_bytes()
    except OSError:
        logger.exception("Cover file read failed")
        return None
