"""Playback position clock that interpolates when providers report zero."""

from __future__ import annotations

import time
from dataclasses import replace

from heartbeat.protocol.models import MediaInfo, MediaState


class MediaClock:
    """Fill in playback position when the platform API returns elapsed 0."""

    def __init__(self) -> None:
        self._track_key = ""
        self._anchor_ms = 0
        self._anchor_mono = time.monotonic()
        self._duration_ms = 0
        self._playing = False

    def decorate(self, info: MediaInfo) -> MediaInfo:
        """Return media info with a best-effort position_ms."""
        key = self._track_key_of(info)
        duration = info.duration_ms or self._duration_ms
        playing = info.state is MediaState.PLAYING
        raw_position = info.position_ms or 0
        now = time.monotonic()
        if key != self._track_key:
            self._track_key = key
            self._anchor_ms = raw_position
            self._anchor_mono = now
        elif raw_position > 0:
            self._anchor_ms = raw_position
            self._anchor_mono = now
        self._duration_ms = duration
        self._playing = playing
        position = raw_position
        if position <= 0 and self._track_key:
            elapsed = int((now - self._anchor_mono) * 1000) if playing else 0
            position = max(self._anchor_ms + elapsed, 0)
        if duration and position > duration:
            position = duration
        return replace(info, position_ms=position, duration_ms=duration or None)

    def _track_key_of(self, info: MediaInfo) -> str:
        return "|".join((info.title or "", info.artist or "", info.album or "", info.app or ""))
