"""macOS osascript 媒体采集"""

from __future__ import annotations

import logging
import subprocess

from heartbeat.adapters.media.selection import prefer_playing
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, MediaInfo, MediaState

logger = logging.getLogger(__name__)

_SEPARATOR = "\x1f"
_IDLE_OUTPUT = "idle"
_TIMEOUT_S = 2.0

_STATE_MAP: dict[str, MediaState] = {
    "playing": MediaState.PLAYING,
    "paused": MediaState.PAUSED,
    "stopped": MediaState.IDLE,
    "idle": MediaState.IDLE,
}

_MUSIC_SCRIPT = """
if application "Music" is not running then return "idle"
tell application "Music"
set st to player state as text
if st is "stopped" then return "idle"
set t to name of current track
set a to artist of current track
set al to album of current track
set d to duration of current track
set p to player position
set dms to (d * 1000) as integer
set pms to (p * 1000) as integer
set sep to (ASCII character 31)
return st & sep & t & sep & a & sep & al & sep & (dms as text) & sep & (pms as text)
end tell
"""

_SPOTIFY_SCRIPT = """
if application "Spotify" is not running then return "idle"
tell application "Spotify"
set st to player state as text
if st is "stopped" then return "idle"
set t to name of current track
set a to artist of current track
set al to album of current track
set d to duration of current track
set pms to (player position * 1000) as integer
set art to artwork url of current track
set sep to (ASCII character 31)
return st & sep & t & sep & a & sep & al & sep & (d as text) & sep & (pms as text) & sep & art
end tell
"""

_APP_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("Music", _MUSIC_SCRIPT),
    ("Spotify", _SPOTIFY_SCRIPT),
)


def parse_script_output(raw: str, app: str) -> MediaInfo:
    """解析 osascript 字段输出，未播放或无法解析时返回 IDLE"""
    text = raw.strip()
    if not text or text == _IDLE_OUTPUT:
        return MediaInfo()
    parts = text.split(_SEPARATOR)
    if len(parts) < 6:
        logger.warning("Unexpected media script output from %s", app)
        return MediaInfo()
    return MediaInfo(
        state=_STATE_MAP.get(parts[0].strip().lower(), MediaState.IDLE),
        title=parts[1] or None,
        artist=parts[2] or None,
        album=parts[3] or None,
        app=app,
        cover_url=parts[6] if len(parts) > 6 and parts[6] else None,
        duration_ms=_as_ms(parts[4]),
        position_ms=_as_ms(parts[5]),
    )


def _as_ms(raw: str) -> int | None:
    value = raw.strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


class MacosMediaAdapter:
    """nowplaying-cli 优先，回落 osascript Music/Spotify"""

    def __init__(self) -> None:
        from heartbeat.adapters.media.nowplaying import NowPlayingMediaAdapter

        self._nowplaying = NowPlayingMediaAdapter()

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集正在播放，隐私关闭时返回 None"""
        if not gate.allow(Capability.MEDIA):
            return None
        if self._nowplaying.available:
            info = self._nowplaying.collect(gate)
            if info is not None and info.state is not MediaState.IDLE:
                return info
        candidates = [self._query(app, script) for app, script in _APP_SCRIPTS]
        return prefer_playing(candidates)

    def _query(self, app: str, script: str) -> MediaInfo:
        output = self._run_osascript(script)
        return parse_script_output(output, app)

    def _run_osascript(self, script: str) -> str:
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            logger.exception("osascript invocation failed")
            return ""
        if result.returncode != 0:
            logger.debug("osascript reported error: %s", result.stderr.strip())
            return ""
        return result.stdout
