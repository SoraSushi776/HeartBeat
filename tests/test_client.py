from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from heartbeat.client.autostart.base import create_provider
from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.paths import config_path, platform_key, secrets_path
from heartbeat.client.config.store import ConfigStore, JsonSecretStore
from heartbeat.client.privacy import PrivacyGate
from heartbeat.client.worker.collector import CollectorWorker
from heartbeat.client.worker.sources import create_collectors, to_adapter_screenshot
from heartbeat.protocol.models import Capability


class ConfigStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp())
        self._store = ConfigStore(self._tmp / "client.json")
        self._secrets = JsonSecretStore(self._tmp / "client.secrets.json")

    def test_roundtrip_and_generated_id(self) -> None:
        config = self._store.load()
        self.assertTrue(config.client_id)
        config.server.base_url = "https://hb.example"
        config.process_whitelist = ["Code"]
        config.setup_completed = True
        self._store.save(config)
        loaded = self._store.load()
        self.assertEqual(loaded.client_id, config.client_id)
        self.assertEqual(loaded.server.base_url, "https://hb.example")
        self.assertEqual(loaded.process_whitelist, ["Code"])
        self.assertTrue(loaded.setup_completed)

    def test_bad_json_falls_back(self) -> None:
        path = self._tmp / "bad.json"
        path.write_text("{oops", encoding="utf-8")
        config = ConfigStore(path).load()
        self.assertTrue(config.client_id)
        self.assertEqual(config.server.base_url, AppConfig().server.base_url)

    def test_secrets_permission(self) -> None:
        self._secrets.save_api_key("token")
        self.assertEqual(self._secrets.load_api_key(), "token")
        mode = (self._tmp / "client.secrets.json").stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_paths(self) -> None:
        self.assertTrue(config_path().name.endswith("client.json"))
        self.assertTrue(secrets_path().name.endswith("client.secrets.json"))
        self.assertIn(platform_key(), {"windows", "macos", "linux"})


class PrivacyGateTest(unittest.TestCase):
    def test_short_circuit_and_events(self) -> None:
        config = AppConfig().privacy
        gate = PrivacyGate(config)
        self.assertTrue(gate.allows(Capability.SCREENSHOT))
        seen: list[bool] = []
        gate.subscribe(lambda flags: seen.append(flags.media))
        gate.set_config(AppConfig.from_dict({"privacy": {"collect_media": False}}).privacy)
        self.assertFalse(gate.allows(Capability.MEDIA))
        self.assertEqual(seen, [False])


class CollectorWorkerTest(unittest.TestCase):
    def test_build_payload_respects_privacy(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        secrets = JsonSecretStore(tmp / "client.secrets.json")
        config = AppConfig.from_dict(
            {
                "client_id": "test-client",
                "privacy": {
                    "collect_screenshot": False,
                    "collect_media": False,
                    "collect_processes": False,
                    "collect_system_load": False,
                },
            }
        )
        gate = PrivacyGate(config.privacy)
        collectors = create_collectors(config.process_whitelist, config.screenshot)
        worker = CollectorWorker(config, secrets, gate, collectors)
        payload, screenshot = worker._build_payload()
        self.assertIsNone(screenshot)
        self.assertIsNone(payload["system"])
        self.assertIsNone(payload["media"])
        self.assertEqual(payload["processes"], [])
        self.assertFalse(payload["privacy"]["screenshot"])

    def test_backoff_table(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        secrets = JsonSecretStore(tmp / "client.secrets.json")
        config = AppConfig()
        gate = PrivacyGate(config.privacy)
        collectors = create_collectors(config.process_whitelist, config.screenshot)
        worker = CollectorWorker(config, secrets, gate, collectors)
        worker._attempt = 0
        self.assertEqual(worker._backoff_seconds(), 0)
        worker._attempt = 2
        self.assertEqual(worker._backoff_seconds(), 15)
        worker._attempt = 99
        self.assertEqual(worker._backoff_seconds(), 300)


class AutostartProviderTest(unittest.TestCase):
    def test_provider_protocol_shape(self) -> None:
        provider = create_provider("python -m heartbeat.client.main")
        for name in ("enable", "disable", "is_enabled"):
            self.assertTrue(callable(getattr(provider, name)))


class SourcesTest(unittest.TestCase):
    def test_create_collectors(self) -> None:
        config = AppConfig()
        bundle = create_collectors(["Code"], config.screenshot)
        self.assertIsNotNone(bundle.screenshot)
        self.assertIsNotNone(bundle.media)
        self.assertIsNotNone(bundle.processes)
        self.assertIsNotNone(bundle.system)

    def test_screenshot_config_mapping(self) -> None:
        config = AppConfig.from_dict(
            {"screenshot": {"blur_radius": 3.5, "scale": 0.5, "quality": 60}}
        )
        adapter_config = to_adapter_screenshot(config.screenshot)
        self.assertEqual(adapter_config.blur_radius, 3.5)
        self.assertEqual(adapter_config.scale, 0.5)
        self.assertEqual(adapter_config.quality, 60)


if __name__ == "__main__":
    unittest.main()
