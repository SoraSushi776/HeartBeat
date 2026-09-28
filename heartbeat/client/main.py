from __future__ import annotations

import logging
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


def launch_command() -> str:
    """Return the command line used for autostart registration."""
    return f"{sys.executable} -m heartbeat.client.main"


def run() -> None:
    """Start the HeartBeat tray client application."""
    setup_logging()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName("HeartBeat")
    app.setApplicationName("HeartBeatClient")

    config_store = ConfigStore(config_path())
    first_run = not config_store.exists()
    secret_store = JsonSecretStore(secrets_path())
    manager = WindowManager.initialize(config_store, secret_store, launch_command())
    config = manager.config
    gate = PrivacyGate(config.privacy)
    collectors = create_collectors(config.process_whitelist, config.screenshot)
    worker = CollectorWorker(config, secret_store, gate, collectors)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    manager.config_saved.connect(worker.apply_config)
    thread.start()

    def handle_quit() -> None:
        QMetaObject.invokeMethod(worker, "stop", Qt.ConnectionType.QueuedConnection)
        thread.wait(5000)
        app.quit()

    tray = TrayController(on_open=manager.show_settings, on_quit=handle_quit)
    tray.show()
    if first_run or not config.ui.start_minimized:
        manager.show_settings()

    logger.info("HeartBeat client started")
    app.exec()
    thread.quit()
    thread.wait(3000)


if __name__ == "__main__":
    run()
