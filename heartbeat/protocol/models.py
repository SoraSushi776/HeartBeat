from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Platform(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class MediaState(str, Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    IDLE = "idle"


class Capability(str, Enum):
    SCREENSHOT = "screenshot"
    MEDIA = "media"
    PROCESSES = "processes"
    SYSTEM = "system"


@dataclass(frozen=True)
class ClientInfo:
    id: str
    platform: Platform
    version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "platform": self.platform.value, "version": self.version}


@dataclass
class SystemInfo:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    load_avg: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "load_avg": list(self.load_avg),
        }


@dataclass
class MediaInfo:
    state: MediaState = MediaState.IDLE
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    app: str | None = None
    cover_url: str | None = None
    position_ms: int | None = None
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "app": self.app,
            "cover_url": self.cover_url,
            "position_ms": self.position_ms,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class ProcessInfo:
    name: str
    count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "count": self.count}


@dataclass
class PrivacyFlags:
    screenshot: bool = True
    media: bool = True
    processes: bool = True
    system: bool = True

    def allows(self, capability: Capability) -> bool:
        mapping: dict[Capability, bool] = {
            Capability.SCREENSHOT: self.screenshot,
            Capability.MEDIA: self.media,
            Capability.PROCESSES: self.processes,
            Capability.SYSTEM: self.system,
        }
        return mapping[capability]

    def to_dict(self) -> dict[str, Any]:
        return {
            "screenshot": self.screenshot,
            "media": self.media,
            "processes": self.processes,
            "system": self.system,
        }


@dataclass
class HeartbeatPayload:
    ts: int
    client: ClientInfo
    system: SystemInfo | None = None
    media: MediaInfo | None = None
    processes: list[ProcessInfo] = field(default_factory=list)
    privacy: PrivacyFlags = field(default_factory=PrivacyFlags)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "ts": self.ts,
            "client": self.client.to_dict(),
            "privacy": self.privacy.to_dict(),
            "processes": [p.to_dict() for p in self.processes],
        }
        data["system"] = self.system.to_dict() if self.system else None
        data["media"] = self.media.to_dict() if self.media else None
        return data


@dataclass(frozen=True)
class ScreenshotResult:
    webp: bytes
    width: int
    height: int


API_PREFIX = "/api/v1"
HEADER_API_KEY = "X-API-Key"
HEADER_CLIENT_VERSION = "X-Client-Version"
HEADER_HEARTBEAT_TS = "X-Heartbeat-Ts"
ONLINE_TIMEOUT_MS = 90_000
DEFAULT_HEARTBEAT_INTERVAL_S = 60
DEFAULT_SCREENSHOT_SCALE = 0.25
DEFAULT_SCREENSHOT_BLUR_RADIUS = 10.0
DEFAULT_SCREENSHOT_QUALITY = 75
DEFAULT_SCREENSHOT_METHOD = 4
