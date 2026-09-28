"""Background worker for setup probes and tool installation."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

from heartbeat.client import setup as setup_checks

logger = logging.getLogger(__name__)


class SetupWorker(QObject):
    """Run setup probes and tool installs away from the UI thread."""

    report_ready = Signal(object)
    install_finished = Signal(bool, str)

    @Slot()
    def refresh_report(self) -> None:
        """Probe tools and permissions and emit the report dict."""
        report = setup_checks.collect_setup_report()
        self.report_ready.emit(report)

    @Slot()
    def install_nowplaying(self) -> None:
        """Install nowplaying-cli via Homebrew and emit the result."""
        logger.info("Installing nowplaying-cli via Homebrew")
        ok, message = setup_checks.run_tool_install()
        if ok:
            logger.info("nowplaying-cli install succeeded")
        else:
            logger.warning("nowplaying-cli install failed: %s", message)
        self.install_finished.emit(ok, message)
