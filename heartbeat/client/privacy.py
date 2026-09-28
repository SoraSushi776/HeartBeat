from __future__ import annotations

from collections.abc import Callable

from heartbeat.adapters.privacy import PrivacyGate as AdapterPrivacyGate
from heartbeat.client.config.models import PrivacyConfig
from heartbeat.protocol.models import Capability, PrivacyFlags

Listener = Callable[[PrivacyFlags], None]


class PrivacyGate:
    """Forward privacy switches to adapters and notify subscribers."""

    def __init__(self, config: PrivacyConfig) -> None:
        self._config = config
        self._adapter_gate = AdapterPrivacyGate(config.to_flags())
        self._listeners: list[Listener] = []

    @property
    def adapter_gate(self) -> AdapterPrivacyGate:
        return self._adapter_gate

    def flags(self) -> PrivacyFlags:
        """Return current privacy flags snapshot."""
        return self._adapter_gate.flags

    def allows(self, capability: Capability) -> bool:
        """Return whether the capability may be collected."""
        return self._adapter_gate.allow(capability)

    def set_config(self, config: PrivacyConfig) -> None:
        """Replace privacy config and notify listeners."""
        self._config = config
        self._adapter_gate.update(config.to_flags())
        flags = self.flags()
        for listener in list(self._listeners):
            listener(flags)

    def subscribe(self, listener: Listener) -> None:
        """Register a listener for privacy flag changes."""
        self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        """Remove a previously registered listener."""
        self._listeners = [item for item in self._listeners if item is not listener]
