"""Windows GSMTC 媒体采集"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

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
    except ImportError:
        return None
    return GlobalSystemMediaTransportControlsSessionManager


def _status_name(status: object) -> str:
    return str(getattr(status, "name", status)).lower()


class WindowsMediaAdapter:
    """winrt GSMTC 会话读取，依赖缺失时降级 IDLE"""

    def __init__(self) -> None:
        self._manager_cls = _load_session_manager_type()

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集正在播放，隐私关闭时返回 None"""
        if not gate.allow(Capability.MEDIA):
            return None
        if self._manager_cls is None:
            logger.warning("winrt media control unavailable, reporting idle")
            return MediaInfo()
        try:
            return asyncio.run(self._fetch())
        except Exception:
            logger.exception("Windows media query failed")
            return MediaInfo()

    async def _fetch(self) -> MediaInfo:
        manager = await self._manager_cls.request_async()
        session = manager.get_current_session()
        if session is None:
            return MediaInfo()
        props = await session.try_get_media_properties_async()
        info = session.get_playback_info()
        timeline = session.get_timeline_properties()
        return MediaInfo(
            state=_STATE_MAP.get(_status_name(info.playback_status), MediaState.IDLE),
            title=props.title or None,
            artist=props.artist or None,
            album=props.album_title or None,
            app=session.source_app_user_model_id or None,
            position_ms=_timedelta_ms(timeline.position),
            duration_ms=_timedelta_ms(timeline.end_time),
        )


def _timedelta_ms(value: object) -> int | None:
    if value is None:
        return None
    total = getattr(value, "total_seconds", None)
    if total is None:
        return None
    return int(total() * 1000)
