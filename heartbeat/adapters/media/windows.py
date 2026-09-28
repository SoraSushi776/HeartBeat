"""Windows GSMTC 媒体采集"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from heartbeat.adapters.media.clock import MediaClock
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, MediaInfo, MediaState

logger = logging.getLogger(__name__)

_STATE_MAP: dict[str, MediaState] = {
    "closed": MediaState.IDLE,
    "opened": MediaState.IDLE,
    "changing": MediaState.PAUSED,
    "stopped": MediaState.IDLE,
    "playing": MediaState.PLAYING,
    "paused": MediaState.PAUSED,
}


def _load_session_manager_type() -> Any | None:
    try:
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager,
        )
    except Exception:
        logger.warning("winrt Windows.Media.Control is not available")
        return None
    return GlobalSystemMediaTransportControlsSessionManager


def _status_name(status: object) -> str:
    return str(getattr(status, "name", status)).lower()


def _timedelta_ms(value: object) -> int | None:
    if value is None:
        return None
    total = getattr(value, "total_seconds", None)
    if total is None:
        return None
    try:
        return int(total() * 1000)
    except Exception:
        return None


class WindowsMediaAdapter:
    """winrt GSMTC 会话读取，依赖缺失时降级 IDLE"""

    def __init__(self) -> None:
        self._manager_cls = _load_session_manager_type()
        self._clock = MediaClock()

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集正在播放，隐私关闭时返回 None"""
        if not gate.allow(Capability.MEDIA):
            return None
        if self._manager_cls is None:
            return MediaInfo()
        try:
            info = self._run_fetch()
        except Exception:
            logger.exception("Windows media query failed")
            return MediaInfo()
        return self._clock.decorate(info)

    def _run_fetch(self) -> MediaInfo:
        try:
            return asyncio.run(self._fetch())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._fetch())
            finally:
                loop.close()

    async def _fetch(self) -> MediaInfo:
        manager = await self._manager_cls.request_async()
        candidates = []
        current = manager.get_current_session()
        if current is not None:
            candidates.append(current)
        try:
            candidates.extend(item for item in (manager.get_sessions() or []) if item is not None)
        except Exception:
            logger.debug("get_sessions failed")
        seen: set[str] = set()
        ordered = []
        for session in candidates:
            key = str(id(session))
            if key in seen:
                continue
            seen.add(key)
            ordered.append(session)
        logger.debug("GSMTC sessions: %d", len(ordered))
        for session in ordered:
            info = await self._read_session(session)
            if info is not None:
                return info
        return MediaInfo()

    async def _read_session(self, session: Any) -> MediaInfo | None:
        try:
            props = await session.try_get_media_properties_async()
        except Exception as exc:
            logger.debug("media properties failed: %s", exc)
            return None
        try:
            info = session.get_playback_info()
            timeline = session.get_timeline_properties()
        except Exception:
            logger.exception("playback info failed")
            return None
        state = _STATE_MAP.get(_status_name(info.playback_status), MediaState.IDLE)
        title = (getattr(props, "title", None) or "").strip() or None
        artist = (getattr(props, "artist", None) or "").strip() or None
        album = (getattr(props, "album_title", None) or "").strip() or None
        app_id = str(getattr(session, "source_app_user_model_id", "") or "")
        if state is MediaState.IDLE and not title:
            return None
        return MediaInfo(
            state=state,
            title=title,
            artist=artist,
            album=album,
            app=_friendly_app_name(app_id),
            position_ms=_timedelta_ms(getattr(timeline, "position", None)),
            duration_ms=_timedelta_ms(getattr(timeline, "end_time", None)),
        )


def _friendly_app_name(app_id: str) -> str | None:
    if not app_id:
        return None
    mapping = {
        "Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic": "Media Player",
        "Microsoft.Media.Player_8wekyb3d8bbwe!Microsoft.Media.Player": "Media Player",
        "Spotify.exe": "Spotify",
        "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify": "Spotify",
        "Chrome.exe": "Chrome",
        "msedge.exe": "Edge",
    }
    return mapping.get(app_id, app_id.split("!")[0] or None)
