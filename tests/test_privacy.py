"""隐私门测试"""

from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import Capability, PrivacyFlags


def test_default_flags_allow_all() -> None:
    gate = PrivacyGate()
    allowed = [gate.allow(capability) for capability in Capability]
    assert all(allowed)


def test_disabled_capability_is_blocked() -> None:
    gate = PrivacyGate(PrivacyFlags(screenshot=False))
    assert not gate.allow(Capability.SCREENSHOT)
    assert gate.allow(Capability.MEDIA)


def test_update_replaces_flags() -> None:
    gate = PrivacyGate()
    gate.update(PrivacyFlags(media=False, processes=False))
    assert not gate.allow(Capability.MEDIA)
    assert not gate.allow(Capability.PROCESSES)
    assert gate.allow(Capability.SYSTEM)


def test_flags_property_returns_snapshot() -> None:
    flags = PrivacyFlags(system=False)
    gate = PrivacyGate(flags)
    assert gate.flags is flags
