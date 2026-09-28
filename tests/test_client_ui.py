"""Offscreen UI construction checks for the client window stack."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from heartbeat.client.config.store import ConfigStore, JsonSecretStore
from heartbeat.client.diagnostics import format_ms, read_cover_bytes
from heartbeat.client.i18n import Translator, tr
from heartbeat.client.markdown import markdown_to_html
from heartbeat.client.window.main_window import MainWindow
from heartbeat.client.window.setup_wizard import SetupWizard
from heartbeat.client.window.window_manager import WindowManager

_APP: QApplication | None = None


def _app() -> QApplication:
    global _APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class HelpersTest(unittest.TestCase):
    def test_tr_lookup(self) -> None:
        self.assertEqual(tr("nav.settings", "zh-CN"), "设置")
        self.assertEqual(tr("nav.settings", "en-US"), "Settings")
        self.assertEqual(tr("nav.settings", "xx-YY"), "Settings")

    def test_markdown_to_html(self) -> None:
        html = markdown_to_html("# Hello\n- item **bold**\n`code`")
        self.assertIn("<h1>Hello</h1>", html)
        self.assertIn("<b>bold</b>", html)
        self.assertIn("<code>code</code>", html)

    def test_format_ms_and_cover(self) -> None:
        self.assertEqual(format_ms(95000), "1:35")
        self.assertEqual(format_ms(None), "--:--")
        self.assertEqual(read_cover_bytes("data:image/png;base64,aGVsbG8="), b"hello")
        self.assertIsNone(read_cover_bytes(None))
        self.assertIsNone(read_cover_bytes("data:image/png;base64,"))


class MainWindowTest(unittest.TestCase):
    def test_construct_resize_and_retranslate(self) -> None:
        app = _app()
        translator = Translator("zh-CN")
        window = MainWindow(translator)
        window.resize(960, 640)
        self.assertEqual(window.size().width(), 960)
        self.assertEqual(window.size().height(), 640)
        window.set_language("en-US")
        self.assertEqual(translator.language, "en-US")
        window.set_language("zh-CN")
        window.close()
        app.processEvents()

    def test_setup_wizard_construct_and_teardown(self) -> None:
        app = _app()
        wizard = SetupWizard(Translator("zh-CN"), "http://127.0.0.1:8000", "key")
        wizard.done(0)
        app.processEvents()


class WindowManagerTest(unittest.TestCase):
    def test_initialize_reads_setup_completed(self) -> None:
        app = _app()
        tmp = Path(tempfile.mkdtemp())
        config_store = ConfigStore(tmp / "client.json")
        manager = WindowManager.initialize(
            config_store,
            JsonSecretStore(tmp / "client.secrets.json"),
            "python -m heartbeat.client.main",
        )
        self.assertFalse(manager.config.setup_completed)
        manager.config.setup_completed = True
        config_store.save(manager.config)
        self.assertTrue(config_store.load().setup_completed)
        manager.shutdown()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
