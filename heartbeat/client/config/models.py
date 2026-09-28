from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from heartbeat.protocol.models import (
    DEFAULT_HEARTBEAT_INTERVAL_S,
    DEFAULT_SCREENSHOT_BLUR_RADIUS,
    DEFAULT_SCREENSHOT_QUALITY,
    DEFAULT_SCREENSHOT_SCALE,
    PrivacyFlags,
)

DEFAULT_BACKOFF_SECONDS: list[int] = [0, 5, 15, 60, 300]


def _as_str(value: Any, default: str) -> str:
    return value if isinstance(value, str) else default


def _as_bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _as_int(value: Any, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _as_float(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    return float(value) if isinstance(value, (int, float)) else default


def _as_str_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _as_int_list(value: Any, default: list[int]) -> list[int]:
    if not isinstance(value, list):
        return list(default)
    items: list[int] = []
    for index, item in enumerate(value):
        fallback = default[index] if index < len(default) else default[-1]
        items.append(_as_int(item, fallback))
    return items or list(default)


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


@dataclass
class ServerConfig:
    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: float = 10.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerConfig:
        return cls(
            base_url=_as_str(data.get("base_url"), cls.base_url),
            timeout_seconds=_as_float(data.get("timeout_seconds"), cls.timeout_seconds),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"base_url": self.base_url, "timeout_seconds": self.timeout_seconds}


@dataclass
class PushConfig:
    enabled: bool = True
    interval_seconds: int = DEFAULT_HEARTBEAT_INTERVAL_S
    retry_backoff_seconds: list[int] = field(default_factory=lambda: list(DEFAULT_BACKOFF_SECONDS))
    max_queue_size: int = 100

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PushConfig:
        return cls(
            enabled=_as_bool(data.get("enabled"), True),
            interval_seconds=_as_int(data.get("interval_seconds"), DEFAULT_HEARTBEAT_INTERVAL_S),
            retry_backoff_seconds=_as_int_list(
                data.get("retry_backoff_seconds"), DEFAULT_BACKOFF_SECONDS
            ),
            max_queue_size=_as_int(data.get("max_queue_size"), 100),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "retry_backoff_seconds": list(self.retry_backoff_seconds),
            "max_queue_size": self.max_queue_size,
        }


@dataclass
class PrivacyConfig:
    collect_screenshot: bool = True
    collect_media: bool = True
    collect_processes: bool = True
    collect_system_load: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrivacyConfig:
        return cls(
            collect_screenshot=_as_bool(data.get("collect_screenshot"), True),
            collect_media=_as_bool(data.get("collect_media"), True),
            collect_processes=_as_bool(data.get("collect_processes"), True),
            collect_system_load=_as_bool(data.get("collect_system_load"), True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "collect_screenshot": self.collect_screenshot,
            "collect_media": self.collect_media,
            "collect_processes": self.collect_processes,
            "collect_system_load": self.collect_system_load,
        }

    def to_flags(self) -> PrivacyFlags:
        return PrivacyFlags(
            screenshot=self.collect_screenshot,
            media=self.collect_media,
            processes=self.collect_processes,
            system=self.collect_system_load,
        )


@dataclass
class ScreenshotConfig:
    blur_radius: float = DEFAULT_SCREENSHOT_BLUR_RADIUS
    scale: float = DEFAULT_SCREENSHOT_SCALE
    quality: int = DEFAULT_SCREENSHOT_QUALITY

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScreenshotConfig:
        return cls(
            blur_radius=_as_float(data.get("blur_radius"), DEFAULT_SCREENSHOT_BLUR_RADIUS),
            scale=_as_float(data.get("scale"), DEFAULT_SCREENSHOT_SCALE),
            quality=_as_int(data.get("quality"), DEFAULT_SCREENSHOT_QUALITY),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "blur_radius": self.blur_radius,
            "scale": self.scale,
            "quality": self.quality,
        }


@dataclass
class AutostartConfig:
    enabled: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutostartConfig:
        return cls(enabled=_as_bool(data.get("enabled"), False))

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": self.enabled}


@dataclass
class UiConfig:
    start_minimized: bool = True
    language: str = "zh-CN"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UiConfig:
        return cls(
            start_minimized=_as_bool(data.get("start_minimized"), True),
            language=_as_str(data.get("language"), "zh-CN"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"start_minimized": self.start_minimized, "language": self.language}


@dataclass
class AppConfig:
    client_id: str = ""
    server: ServerConfig = field(default_factory=ServerConfig)
    push: PushConfig = field(default_factory=PushConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    process_whitelist: list[str] = field(default_factory=list)
    process_collect_all: bool = True
    autostart: AutostartConfig = field(default_factory=AutostartConfig)
    ui: UiConfig = field(default_factory=UiConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        return cls(
            client_id=_as_str(data.get("client_id"), ""),
            server=ServerConfig.from_dict(_section(data, "server")),
            push=PushConfig.from_dict(_section(data, "push")),
            privacy=PrivacyConfig.from_dict(_section(data, "privacy")),
            screenshot=ScreenshotConfig.from_dict(_section(data, "screenshot")),
            process_whitelist=_as_str_list(data.get("process_whitelist")),
            process_collect_all=_as_bool(data.get("process_collect_all"), True),
            autostart=AutostartConfig.from_dict(_section(data, "autostart")),
            ui=UiConfig.from_dict(_section(data, "ui")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "server": self.server.to_dict(),
            "push": self.push.to_dict(),
            "privacy": self.privacy.to_dict(),
            "screenshot": self.screenshot.to_dict(),
            "process_whitelist": list(self.process_whitelist),
            "process_collect_all": self.process_collect_all,
            "autostart": self.autostart.to_dict(),
            "ui": self.ui.to_dict(),
        }
