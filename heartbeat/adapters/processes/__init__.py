"""进程采集"""

from collections.abc import Sequence

from heartbeat.adapters.base import ProcessAdapter
from heartbeat.adapters.processes.collector import PsutilProcessAdapter
from heartbeat.adapters.processes.filter import ProcessFilter


def get_process_adapter(patterns: Sequence[str] = (), collect_all: bool = False) -> ProcessAdapter:
    """返回进程采集适配器，collect_all 为真时采集除排除表外全部进程"""
    return PsutilProcessAdapter(ProcessFilter(patterns, collect_all=collect_all))


__all__ = ["ProcessFilter", "get_process_adapter"]
