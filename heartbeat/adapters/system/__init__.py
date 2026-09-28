"""系统负载采集"""

from heartbeat.adapters.base import SystemAdapter
from heartbeat.adapters.system.collector import PsutilSystemAdapter


def get_system_adapter() -> SystemAdapter:
    """返回系统负载采集适配器"""
    return PsutilSystemAdapter()


__all__ = ["get_system_adapter"]
