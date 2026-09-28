"""隐私开关门"""

from __future__ import annotations

from heartbeat.protocol.models import Capability, PrivacyFlags


class PrivacyGate:
    """隐私门，关闭的能力在采集入口短路"""

    def __init__(self, flags: PrivacyFlags | None = None) -> None:
        self._flags = flags or PrivacyFlags()

    @property
    def flags(self) -> PrivacyFlags:
        """当前隐私开关快照"""
        return self._flags

    def update(self, flags: PrivacyFlags) -> None:
        """替换隐私开关配置"""
        self._flags = flags

    def allow(self, capability: Capability) -> bool:
        """查询 capability 是否允许采集"""
        return self._flags.allows(capability)
