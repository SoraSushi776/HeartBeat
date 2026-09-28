from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from heartbeat.adapters.platform import current_platform
from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.store import SecretStore
from heartbeat.client.privacy import PrivacyGate
from heartbeat.client.worker.sources import CollectorBundle, create_collectors
from heartbeat.protocol.models import (
    API_PREFIX,
    HEADER_API_KEY,
    HEADER_CLIENT_VERSION,
    HEADER_HEARTBEAT_TS,
    ClientInfo,
    HeartbeatPayload,
    MediaInfo,
    ProcessInfo,
    ScreenshotResult,
    SystemInfo,
)

logger = logging.getLogger(__name__)


class CollectorWorker(QObject):
    """Collect local state on a timer and push heartbeats to the server."""

    snapshot_ready = Signal(object)
    push_succeeded = Signal(float)
    push_failed = Signal(str, int)
    finished = Signal()

    def __init__(
        self,
        config: AppConfig,
        secrets: SecretStore,
        gate: PrivacyGate,
        collectors: CollectorBundle,
    ) -> None:
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._gate = gate
        self._collectors = collectors
        self._attempt = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    @Slot()
    def run(self) -> None:
        """Start the periodic collection timer."""
        if not self._config.push.enabled:
            logger.info("Push disabled, worker idle")
            return
        self._timer.start(self._interval_ms())
        self._on_tick()
        logger.info("Collector worker started")

    @Slot()
    def stop(self) -> None:
        """Stop the timer and signal thread teardown."""
        self._timer.stop()
        self.finished.emit()
        logger.info("Collector worker stopped")

    @Slot(object)
    def apply_config(self, config: AppConfig) -> None:
        """Replace runtime config and restart scheduling when needed."""
        self._config = config
        self._gate.set_config(config.privacy)
        self._collectors = create_collectors(config.process_whitelist, config.screenshot)
        if not config.push.enabled:
            self._timer.stop()
            return
        self._timer.start(self._interval_ms())

    def _interval_ms(self) -> int:
        return max(int(self._config.push.interval_seconds * 1000), 1000)

    @Slot()
    def _on_tick(self) -> None:
        payload, screenshot = self._build_payload()
        self.snapshot_ready.emit(payload)
        self._push_payload(payload, screenshot)

    def _build_payload(self) -> tuple[dict[str, Any], ScreenshotResult | None]:
        flags = self._gate.flags()
        client = ClientInfo(id=self._config.client_id, platform=current_platform())
        screenshot = self._collect_screenshot()
        payload = HeartbeatPayload(
            ts=int(time.time() * 1000),
            client=client,
            system=self._collect_system(),
            media=self._collect_media(),
            processes=self._collect_processes(),
            privacy=flags,
        )
        return payload.to_dict(), screenshot

    def _collect_screenshot(self) -> ScreenshotResult | None:
        return self._collectors.screenshot.collect(self._gate.adapter_gate)

    def _collect_system(self) -> SystemInfo | None:
        return self._collectors.system.collect(self._gate.adapter_gate)

    def _collect_media(self) -> MediaInfo | None:
        return self._collectors.media.collect(self._gate.adapter_gate)

    def _collect_processes(self) -> list[ProcessInfo]:
        return self._collectors.processes.collect(self._gate.adapter_gate) or []

    def _push_payload(self, payload: dict[str, Any], screenshot: ScreenshotResult | None) -> None:
        data = self._post_heartbeat(payload)
        if data is None:
            self._attempt += 1
            delay = self._backoff_seconds()
            self._timer.start(max(delay, 1) * 1000)
            self.push_failed.emit("heartbeat", self._attempt)
            logger.warning("Heartbeat failed, attempt=%s delay=%ss", self._attempt, delay)
            return
        self._attempt = 0
        self._timer.start(self._interval_ms())
        self.push_succeeded.emit(float(payload.get("ts", 0)))
        upload_url = data.get("screenshot_upload_url")
        if upload_url and screenshot is not None:
            self._put_screenshot(str(upload_url), payload.get("ts"), screenshot)

    def _backoff_seconds(self) -> int:
        table = self._config.push.retry_backoff_seconds
        return table[min(self._attempt, len(table) - 1)]

    def _headers(self) -> dict[str, str]:
        return {
            HEADER_API_KEY: self._secrets.load_api_key(),
            HEADER_CLIENT_VERSION: "0.1.0",
        }

    def _base_url(self) -> str:
        return self._config.server.base_url.rstrip("/")

    def _post_heartbeat(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self._base_url()}{API_PREFIX}/heartbeat"
        try:
            response = httpx.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self._config.server.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Heartbeat request error")
            return None
        body = response.json()
        if not isinstance(body, dict):
            return None
        data = body.get("data")
        return data if isinstance(data, dict) else {}

    def _put_screenshot(self, upload_url: str, ts: Any, screenshot: ScreenshotResult) -> None:
        url = upload_url
        if upload_url.startswith("/"):
            url = f"{self._base_url()}{upload_url}"
        headers = self._headers()
        headers["Content-Type"] = "image/webp"
        if isinstance(ts, int):
            headers[HEADER_HEARTBEAT_TS] = str(ts)
        try:
            response = httpx.put(
                url,
                content=screenshot.webp,
                headers=headers,
                timeout=self._config.server.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Screenshot upload failed")
            self.push_failed.emit("screenshot", self._attempt)
