"""First-run setup wizard for tools, permissions, and server credentials."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QMetaObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from heartbeat.client import setup as setup_checks
from heartbeat.client.i18n import Translator
from heartbeat.client.worker.setup import SetupWorker

logger = logging.getLogger(__name__)


class SetupWizard(QWizard):
    """Guide the user through tool install, permissions, and server config."""

    setup_finished = Signal(str, str)

    def __init__(
        self,
        translator: Translator,
        base_url: str,
        api_key: str,
    ) -> None:
        super().__init__()
        self._t = translator
        self.setWindowTitle(self._t.tr("setup.window_title"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.resize(560, 420)
        self._nowplaying_label = QLabel()
        self._brew_label = QLabel()
        self._screen_label = QLabel()
        self._automation_label = QLabel()
        self._install_button = QPushButton()
        self._screen_button = QPushButton()
        self._automation_button = QPushButton()
        self._recheck_button = QPushButton()
        self._url_edit = QLineEdit(base_url)
        self._api_key_edit = QLineEdit(api_key)
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._installing = False
        self._thread = QThread()
        self._worker = SetupWorker()
        self._worker.moveToThread(self._thread)
        self._thread.start()
        self._build_pages()
        self.retranslate()
        self._wire()
        self._request_report()

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self.setWindowTitle(self._t.tr("setup.window_title"))
        self.setButtonText(QWizard.WizardButton.NextButton, self._t.tr("button.save"))
        self.setButtonText(QWizard.WizardButton.FinishButton, self._t.tr("button.save"))
        self._tools_page.setTitle(self._t.tr("setup.page_tools"))
        self._perms_page.setTitle(self._t.tr("setup.page_perms"))
        self._server_page.setTitle(self._t.tr("setup.page_server"))
        self._tools_intro.setText(self._t.tr("setup.tools_intro"))
        self._perms_intro.setText(self._t.tr("setup.perms_intro"))
        self._server_intro.setText(self._t.tr("setup.server_intro"))
        self._finish_hint.setText(self._t.tr("setup.finish_hint"))
        self._nowplaying_caption.setText(self._t.tr("setup.nowplaying"))
        self._brew_caption.setText(self._t.tr("setup.homebrew"))
        self._screen_caption.setText(self._t.tr("setup.screen_recording"))
        self._automation_caption.setText(self._t.tr("setup.automation"))
        self._install_button.setText(self._t.tr("setup.install_nowplaying"))
        self._screen_button.setText(self._t.tr("setup.open_screen_settings"))
        self._automation_button.setText(self._t.tr("setup.open_automation_settings"))
        self._recheck_button.setText(self._t.tr("button.recheck"))
        self._url_label.setText(self._t.tr("settings.base_url"))
        self._api_key_label.setText(self._t.tr("settings.api_key"))

    def accept(self) -> None:
        """Emit the finished configuration and close the wizard."""
        self.setup_finished.emit(self._url_edit.text().strip(), self._api_key_edit.text().strip())
        super().accept()

    def done(self, result: int) -> None:
        """Stop the setup worker thread and close the wizard."""
        self._thread.quit()
        self._thread.wait(3000)
        super().done(result)

    @Slot(object)
    def apply_report(self, report: object) -> None:
        """Update tool and permission status labels from a probe report."""
        data = report if isinstance(report, dict) else {}
        tools = {
            str(item.get("name")): item
            for item in data.get("tools", [])
            if isinstance(item, dict)
        }
        permissions = {
            str(item.get("name")): item
            for item in data.get("permissions", [])
            if isinstance(item, dict)
        }
        self._nowplaying_label.setText(self._status_text(tools.get("nowplaying-cli")))
        self._brew_label.setText(self._status_text(tools.get("homebrew")))
        self._screen_label.setText(self._status_text(permissions.get("screen_recording")))
        self._automation_label.setText(self._status_text(permissions.get("automation")))

    @Slot(bool, str)
    def apply_install_result(self, ok: bool, message: str) -> None:
        """Handle the install worker result and refresh the report."""
        self._installing = False
        self._install_button.setEnabled(True)
        if ok:
            self._install_button.setText(self._t.tr("setup.install_ok"))
            logger.info("Setup install finished")
        else:
            self._install_button.setText(self._t.tr("setup.install_failed"))
            QMessageBox.warning(self, self._t.tr("error.title"), message)
            logger.warning("Setup install reported failure")
        self._request_report()

    def _build_pages(self) -> None:
        self._tools_intro = QLabel()
        self._tools_intro.setWordWrap(True)
        self._perms_intro = QLabel()
        self._perms_intro.setWordWrap(True)
        self._server_intro = QLabel()
        self._server_intro.setWordWrap(True)
        self._finish_hint = QLabel()
        self._finish_hint.setWordWrap(True)
        self._nowplaying_caption = QLabel()
        self._brew_caption = QLabel()
        self._screen_caption = QLabel()
        self._automation_caption = QLabel()
        self._url_label = QLabel()
        self._api_key_label = QLabel()
        self._tools_page = QWizardPage()
        self._perms_page = QWizardPage()
        self._server_page = QWizardPage()
        tools_form = QFormLayout()
        tools_form.addRow(self._nowplaying_caption, self._nowplaying_label)
        tools_form.addRow(self._brew_caption, self._brew_label)
        tools_form.addRow(self._install_button)
        tools_layout = QVBoxLayout(self._tools_page)
        tools_layout.addWidget(self._tools_intro)
        tools_layout.addLayout(tools_form)
        tools_layout.addStretch(1)
        perms_form = QFormLayout()
        perms_form.addRow(self._screen_caption, self._screen_label)
        perms_form.addRow(self._screen_button)
        perms_form.addRow(self._automation_caption, self._automation_label)
        perms_form.addRow(self._automation_button)
        perms_form.addRow(self._recheck_button)
        perms_layout = QVBoxLayout(self._perms_page)
        perms_layout.addWidget(self._perms_intro)
        perms_layout.addLayout(perms_form)
        perms_layout.addStretch(1)
        server_form = QFormLayout()
        server_form.addRow(self._url_label, self._url_edit)
        server_form.addRow(self._api_key_label, self._api_key_edit)
        server_layout = QVBoxLayout(self._server_page)
        server_layout.addWidget(self._server_intro)
        server_layout.addLayout(server_form)
        server_layout.addWidget(self._finish_hint)
        server_layout.addStretch(1)
        self.addPage(self._tools_page)
        self.addPage(self._perms_page)
        self.addPage(self._server_page)

    def _wire(self) -> None:
        self._worker.report_ready.connect(self.apply_report)
        self._worker.install_finished.connect(self.apply_install_result)
        self._install_button.clicked.connect(self._on_install_clicked)
        self._screen_button.clicked.connect(setup_checks.open_screen_recording_settings)
        self._automation_button.clicked.connect(setup_checks.open_automation_settings)
        self._recheck_button.clicked.connect(self._request_report)

    def _request_report(self) -> None:
        QMetaObject.invokeMethod(
            self._worker, "refresh_report", Qt.ConnectionType.QueuedConnection
        )

    def _request_install(self) -> None:
        QMetaObject.invokeMethod(
            self._worker, "install_nowplaying", Qt.ConnectionType.QueuedConnection
        )

    def _on_install_clicked(self) -> None:
        answer = QMessageBox.question(
            self,
            self._t.tr("setup.install_confirm_title"),
            self._t.tr("setup.install_confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._installing = True
        self._install_button.setEnabled(False)
        self._install_button.setText(self._t.tr("setup.installing"))
        self._request_install()

    def _status_text(self, entry: dict[str, Any] | None) -> str:
        if entry is None:
            return self._t.tr("status.unknown")
        status = str(entry.get("status", "unknown"))
        return self._t.tr(f"status.{status}")
