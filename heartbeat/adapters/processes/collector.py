"""psutil 进程列表采集"""

from __future__ import annotations

import logging

import psutil

from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.adapters.processes.filter import ProcessFilter, aggregate, aggregate_key
from heartbeat.protocol.models import Capability, ProcessInfo

logger = logging.getLogger(__name__)

_FETCH_ATTRS = ("name", "exe", "cmdline", "status")


class PsutilProcessAdapter:
    """psutil 遍历进程并按白名单过滤聚合"""

    def __init__(self, process_filter: ProcessFilter | None = None) -> None:
        self._filter = process_filter or ProcessFilter()

    def collect(self, gate: PrivacyGate) -> list[ProcessInfo] | None:
        """采集白名单进程，隐私关闭时返回 None"""
        if not gate.allow(Capability.PROCESSES):
            return None
        if not self._filter.enabled:
            return []
        return aggregate(self._matched_names())

    def _matched_names(self) -> list[str]:
        matched: list[str] = []
        for process in psutil.process_iter(_FETCH_ATTRS):
            name, exe, cmdline0, status = self._read(process)
            if not name:
                continue
            if status == psutil.STATUS_ZOMBIE:
                continue
            if self._filter.matches(name, exe, cmdline0):
                matched.append(aggregate_key(name, exe, cmdline0))
        return matched

    def _read(self, process: psutil.Process) -> tuple[str, str | None, str | None, str | None]:
        try:
            info = process.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "", None, None, None
        cmdline = info.get("cmdline") or []
        cmdline0 = cmdline[0] if cmdline else None
        return info.get("name") or "", info.get("exe"), cmdline0, info.get("status")
