"""Linux MPRIS2 媒体采集"""

from __future__ import annotations

import logging
from typing import Any

from heartbeat.adapters.media.selection import prefer_playing
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, MediaInfo, MediaState

logger = logging.getLogger(__name__)

_PLAYER_PREFIX = "org.mpris.MediaPlayer2."
_OBJECT_PATH = "/org/mpris/MediaPlayer2"
_PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
_DBUS_NAME = "org.freedesktop.DBus"
_DBUS_PATH = "/org/freedesktop/DBus"
_STATE_MAP: dict[str, MediaState] = {
    "playing": MediaState.PLAYING,
    "paused": MediaState.PAUSED,
    "stopped": MediaState.IDLE,
}


def parse_metadata(metadata: dict[Any, Any], status: str, app: str) -> MediaInfo:
    """解析 MPRIS Metadata 与 PlaybackStatus 为 MediaInfo"""
    length_us = metadata.get("mpris:length")
    position_us = metadata.get("mpris:position")
    return MediaInfo(
        state=_STATE_MAP.get(status.strip().lower(), MediaState.IDLE),
        title=_text(metadata.get("xesam:title")),
        artist=_artist_text(metadata.get("xesam:artist")),
        album=_text(metadata.get("xesam:album")),
        app=app,
        cover_url=_text(metadata.get("mpris:artUrl")),
        duration_ms=_us_to_ms(length_us),
        position_ms=_us_to_ms(position_us),
    )


def _text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _artist_text(value: object) -> str | None:
    if isinstance(value, (list, tuple)):
        joined = ", ".join(str(item) for item in value).strip()
        return joined or None
    return _text(value)


def _us_to_ms(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(int(value) / 1000)
    except (TypeError, ValueError):
        return None


class LinuxMediaAdapter:
    """jeepney 读取 MPRIS2 会话总线"""

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集正在播放，隐私关闭时返回 None"""
        if not gate.allow(Capability.MEDIA):
            return None
        try:
            candidates = self._query_players()
        except Exception:
            logger.exception("MPRIS query failed")
            return MediaInfo()
        return prefer_playing(candidates)

    def _query_players(self) -> list[MediaInfo]:
        connection = self._open_connection()
        if connection is None:
            return []
        with connection:
            names = self._list_player_names(connection)
            found = [self._read_player(connection, name) for name in names]
            return [info for info in found if info]

    def _open_connection(self) -> Any:
        try:
            from jeepney.io.blocking import open_dbus_connection
        except ImportError:
            logger.warning("jeepney unavailable, reporting idle")
            return None
        try:
            return open_dbus_connection(bus="SESSION")
        except Exception:
            logger.exception("session bus connection failed")
            return None

    def _list_player_names(self, connection: Any) -> list[str]:
        from jeepney import DBusAddress, new_method_call

        address = DBusAddress(_DBUS_PATH, bus_name=_DBUS_NAME, interface=_DBUS_NAME)
        message = new_method_call(address, "ListNames")
        reply = connection.send_and_get_reply(message)
        names = reply.body[0] if reply.body else []
        return [name for name in names if name.startswith(_PLAYER_PREFIX)]

    def _read_player(self, connection: Any, bus_name: str) -> MediaInfo | None:
        properties = self._get_all(connection, bus_name)
        if not properties:
            return None
        status = str(properties.get("PlaybackStatus", "Stopped"))
        metadata = properties.get("Metadata") or {}
        app = bus_name.removeprefix(_PLAYER_PREFIX)
        info = parse_metadata(dict(metadata), status, app)
        if info.state is MediaState.IDLE:
            return None
        return info

    def _get_all(self, connection: Any, bus_name: str) -> dict[str, Any]:
        from jeepney import DBusAddress, new_method_call

        address = DBusAddress(
            _OBJECT_PATH,
            bus_name=bus_name,
            interface=_PROPERTIES_INTERFACE,
        )
        message = new_method_call(address, "GetAll", "s", (_PLAYER_INTERFACE,))
        try:
            reply = connection.send_and_get_reply(message)
        except Exception:
            logger.debug("MPRIS GetAll failed for %s", bus_name)
            return {}
        if not reply.body:
            return {}
        return dict(reply.body[0])
