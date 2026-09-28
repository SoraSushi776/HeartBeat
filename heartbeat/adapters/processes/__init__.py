"""进程采集"""

from collections.abc import Sequence

from heartbeat.adapters.base import ProcessAdapter
from heartbeat.adapters.processes.collector import PsutilProcessAdapter
from heartbeat.adapters.processes.filter import ProcessFilter


def get_process_adapter(patterns: Sequence[str] = ()) -> ProcessAdapter:
    """返回进程采集适配器，patterns 为正则白名单，空名单不采集"""
    return PsutilProcessAdapter(ProcessFilter(patterns))


__all__ = ["ProcessFilter", "get_process_adapter"]
