"""媒体候选择优"""

from __future__ import annotations

from collections.abc import Sequence

from heartbeat.protocol.models import MediaInfo, MediaState

_STATE_RANK: dict[MediaState, int] = {
    MediaState.PLAYING: 2,
    MediaState.PAUSED: 1,
    MediaState.IDLE: 0,
}


def prefer_playing(candidates: Sequence[MediaInfo]) -> MediaInfo:
    """多播放器候选中优先返回正在播放项，否则返回 IDLE"""
    return max(candidates, key=lambda info: _STATE_RANK[info.state], default=MediaInfo())
