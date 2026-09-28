"""macOS nowplaying-cli 媒体采集"""

from __future__ import annotations

import base64
import json
import logging
import shutil
import subprocess

from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, MediaInfo, MediaState

logger = logging.getLogger(__name__)

_BINARY_CANDIDATES: tuple[str, ...] = (
    "nowplaying-cli",
    "/opt/homebrew/bin/nowplaying-cli",
    "/usr/local/bin/nowplaying-cli",
)

_TIMEOUT_S = 2.0
_ARTWORK_MAX_BYTES = 24_000

_STATE_BY_RATE: dict[bool, MediaState] = {
    True: MediaState.PLAYING,
    False: MediaState.PAUSED,
}


def resolve_binary() -> str | None:
    for candidate in _BINARY_CANDIDATES:
        path = shutil.which(candidate) if "/" not in candidate else candidate
        if path and _is_executable(path):
            return path
    return None


def _is_executable(path: str) -> bool:
    import os

    return os.path.isfile(path) and os.access(path, os.X_OK)


def parse_nowplaying_json(raw: str) -> MediaInfo:
    """解析 nowplaying-cli get --json 输出"""
    text = raw.strip()
    if not text:
        return MediaInfo()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Invalid nowplaying json")
        return MediaInfo()
    if not isinstance(data, dict):
        return MediaInfo()
    title = _as_str(data.get("title"))
    artist = _as_str(data.get("artist"))
    album = _as_str(data.get("album"))
    rate = data.get("playbackRate")
    playing = isinstance(rate, (int, float)) and rate > 0
    if not title and not artist:
        return MediaInfo()
    return MediaInfo(
        state=_STATE_BY_RATE.get(playing, MediaState.PAUSED) if playing or rate else MediaState.IDLE,
        title=title,
        artist=artist,
        album=album,
        app=_app_name(data.get("clientBundleIdentifier")),
        cover_url=_artwork_data_url(data.get("artworkData")),
        duration_ms=_seconds_to_ms(data.get("duration")),
        position_ms=_seconds_to_ms(data.get("elapsedTime")),
    )


def _as_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _app_name(bundle: object) -> str | None:
    text = _as_str(bundle)
    if not text:
        return None
    mapping = {
        "top.imsyy.splayer-next": "SPlayer",
        "com.apple.Music": "Music",
        "com.spotify.client": "Spotify",
    }
    return mapping.get(text, text.rsplit(".", 1)[-1])


def _seconds_to_ms(value: object) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    return int(float(value) * 1000)


def _artwork_data_url(value: object) -> str | None:
    text = _as_str(value)
    if not text:
        return None
    try:
        raw = base64.b64decode(text)
    except (ValueError, TypeError):
        return None
    if not raw:
        return None
    if len(raw) > _ARTWORK_MAX_BYTES:
        raw = raw[:_ARTWORK_MAX_BYTES]
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


class NowPlayingMediaAdapter:
    """nowplaying-cli 读取系统 Now Playing"""

    def __init__(self, binary: str | None = None) -> None:
        self._binary = binary or resolve_binary()

    @property
    def available(self) -> bool:
        return self._binary is not None

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集系统正在播放，隐私关闭时返回 None"""
        if not gate.allow(Capability.MEDIA):
            return None
        if not self._binary:
            return MediaInfo()
        output = self._run(self._binary)
        return parse_nowplaying_json(output)

    def _run(self, binary: str) -> str:
        try:
            result = subprocess.run(
                [
                    binary,
                    "get",
                    "--json",
                    "title",
                    "artist",
                    "album",
                    "elapsedTime",
                    "duration",
                    "playbackRate",
                    "clientBundleIdentifier",
                    "artworkData",
                ],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            logger.exception("nowplaying-cli invocation failed")
            return ""
        if result.returncode != 0:
            logger.debug("nowplaying-cli error: %s", result.stderr.strip())
            return ""
        return result.stdout
