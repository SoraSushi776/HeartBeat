from __future__ import annotations

import logging
import os
import subprocess
import sys

from PySide6.QtCore import QMetaObject, Qt, QThread
from PySide6.QtWidgets import QApplication

from heartbeat.client.config.paths import config_path, secrets_path
from heartbeat.client.config.store import ConfigStore, JsonSecretStore
from heartbeat.client.privacy import PrivacyGate
from heartbeat.client.tray import TrayController
from heartbeat.client.window.window_manager import WindowManager
from heartbeat.client.worker.collector import CollectorWorker
from heartbeat.client.worker.sources import create_collectors
from heartbeat.logging_util import setup_logging

logger = logging.getLogger(__name__)


def launch_arguments() -> list[str]:
    """Return argv used for autostart registration."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, "-m", "heartbeat.client.main"]


def launch_command() -> str:
    """Return the shell command line used for autostart registration."""
    return subprocess.list2cmdline(launch_arguments()) if os.name == "nt" else " ".join(
        _shell_quote(part) for part in launch_arguments()
    )


def _shell_quote(value: str) -> str:
    if not value or any(ch in value for ch in ' "\'\\$`'):
        return "'" + value.replace("'", "'\"'\"'") + "'"
    return value


def _hide_dock_on_macos() -> None:
    if sys.platform != "darwin":
        return
    try:
        import ctypes

        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.dylib")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        def send_void(receiver: int | None, selector: bytes, *args: int) -> int | None:
            if not args:
                return objc.objc_msgSend(receiver, objc.sel_registerName(selector))
            objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
            return objc.objc_msgSend(receiver, objc.sel_registerName(selector), args[0])

        cls = objc.objc_getClass(b"NSApplication")
        ns_app = send_void(cls, b"sharedApplication")
        send_void(ns_app, b"setActivationPolicy:", 1)
    except Exception:
        logger.exception("macOS dock hide failed")


def run() -> None:
    """Start the HeartBeat tray client application."""
    setup_logging()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _hide_dock_on_macos()
    app.setOrganizationName("HeartBeat")
    app.setApplicationName("HeartBeatClient")

    config_store = ConfigStore(config_path())
    first_run = not config_store.exists()
    secret_store = JsonSecretStore(secrets_path())
    manager = WindowManager.initialize(config_store, secret_store, launch_arguments())
    config = manager.config
    gate = PrivacyGate(config.privacy)
    collectors = create_collectors(
        config.process_whitelist, config.screenshot, config.process_collect_all
    )
    worker = CollectorWorker(config, secret_store, gate, collectors)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    manager.config_saved.connect(worker.apply_config)
    window = manager.main_window
    worker.diagnostics_ready.connect(window.apply_diagnostics)
    worker.push_succeeded.connect(window.record_push_success)
    worker.push_failed.connect(window.record_push_failure)
    window.diagnostics_refresh_requested.connect(
        lambda: QMetaObject.invokeMethod(
            worker, "collect_diagnostics", Qt.ConnectionType.QueuedConnection
        )
    )
    thread.start()

    def handle_quit() -> None:
        QMetaObject.invokeMethod(worker, "stop", Qt.ConnectionType.QueuedConnection)
        thread.wait(5000)
        manager.shutdown()
        app.quit()

    tray = TrayController(on_open=manager.show_settings, on_quit=handle_quit)
    tray.retranslate(config.ui.language)
    manager.language_changed.connect(tray.retranslate)
    tray.show()
    if first_run or not config.setup_completed:
        manager.show_setup_wizard()
    if first_run or not config.ui.start_minimized:
        manager.show_settings()

    logger.info("HeartBeat client started")
    app.exec()
    thread.quit()
    thread.wait(3000)
    manager.shutdown()


if __name__ == "__main__":
    run()
