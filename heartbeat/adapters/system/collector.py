"""psutil 系统负载采集"""

from __future__ import annotations

import os
from collections.abc import Callable

import psutil

from heartbeat.adapters.platform import current_platform
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, Platform, SystemInfo


def _unix_load_avg() -> list[float]:
    return list(os.getloadavg())


def _empty_load_avg() -> list[float]:
    return []


_LOAD_AVG_GETTERS: dict[Platform, Callable[[], list[float]]] = {
    Platform.WINDOWS: _empty_load_avg,
    Platform.MACOS: _unix_load_avg,
    Platform.LINUX: _unix_load_avg,
}


class PsutilSystemAdapter:
    """cpu_percent 与 virtual_memory 采集，Unix 附带负载均值"""

    def collect(self, gate: PrivacyGate) -> SystemInfo | None:
        """采集系统负载，隐私关闭时返回 None"""
        if not gate.allow(Capability.SYSTEM):
            return None
        memory = psutil.virtual_memory()
        return SystemInfo(
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_percent=memory.percent,
            load_avg=_LOAD_AVG_GETTERS[current_platform()](),
        )
