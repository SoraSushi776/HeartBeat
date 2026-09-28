from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication

from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.store import JsonSecretStore
from heartbeat.client.privacy import PrivacyGate
from heartbeat.client.worker.collector import CollectorWorker
from heartbeat.client.worker.sources import create_collectors


def main() -> int:
    app = QApplication([])
    tmp = Path(tempfile.mkdtemp())
    secrets = JsonSecretStore(tmp / "client.secrets.json")
    config = AppConfig()
    config.push.enabled = False
    collectors = create_collectors(config.process_whitelist, config.screenshot)
    worker = CollectorWorker(config, secrets, PrivacyGate(config.privacy), collectors)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    thread.start()
    QTimer.singleShot(200, worker.stop)
    QTimer.singleShot(250, thread.quit)
    QTimer.singleShot(2000, app.quit)
    app.exec()
    finished = thread.wait(3000)
    print("thread_stopped", finished and not thread.isRunning())
    return 0 if finished else 1


if __name__ == "__main__":
    sys.exit(main())
