from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.config.models import AppConfig


class SettingsView(QWidget):
    """Settings form assembled in code and driven entirely by config fields."""

    save_requested = Signal(object, str)
    close_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._base: AppConfig = AppConfig()
        self.setWindowTitle("HeartBeat Settings")
        self._url_edit = QLineEdit()
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._push_enabled = QCheckBox("Enable push")
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(5, 3600)
        self._collect_screenshot = QCheckBox("Screenshot")
        self._collect_media = QCheckBox("Media")
        self._collect_processes = QCheckBox("Processes")
        self._collect_system = QCheckBox("System load")
        self._blur_spin = QDoubleSpinBox()
        self._blur_spin.setRange(0.0, 100.0)
        self._blur_spin.setSingleStep(0.5)
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.05, 1.0)
        self._scale_spin.setSingleStep(0.05)
        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(1, 100)
        self._whitelist_edit = QLineEdit()
        self._whitelist_edit.setPlaceholderText("Code, Safari")
        self._autostart_check = QCheckBox("Start at login")
        self._start_minimized = QCheckBox("Start minimized to tray")
        self._save_button = QPushButton("Save")
        self._cancel_button = QPushButton("Close")
        self._build_layout()
        self._save_button.clicked.connect(self._on_save)
        self._cancel_button.clicked.connect(self.close_requested.emit)

    def apply_config(self, config: AppConfig, api_key: str) -> None:
        """Load config values into the form widgets."""
        self._base = config
        self._url_edit.setText(config.server.base_url)
        self._api_key_edit.setText(api_key)
        self._push_enabled.setChecked(config.push.enabled)
        self._interval_spin.setValue(config.push.interval_seconds)
        self._collect_screenshot.setChecked(config.privacy.collect_screenshot)
        self._collect_media.setChecked(config.privacy.collect_media)
        self._collect_processes.setChecked(config.privacy.collect_processes)
        self._collect_system.setChecked(config.privacy.collect_system_load)
        self._blur_spin.setValue(config.screenshot.blur_radius)
        self._scale_spin.setValue(config.screenshot.scale)
        self._quality_spin.setValue(config.screenshot.quality)
        self._whitelist_edit.setText(", ".join(config.process_whitelist))
        self._autostart_check.setChecked(config.autostart.enabled)
        self._start_minimized.setChecked(config.ui.start_minimized)

    def is_visible(self) -> bool:
        """Return whether the settings window is currently shown."""
        return self.isVisible()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Hide the window instead of destroying it on close."""
        self.close_requested.emit()
        event.accept()

    def _on_save(self) -> None:
        self._apply_form()
        api_key = self._api_key_edit.text().strip()
        self.save_requested.emit(self._base, api_key)

    def _apply_form(self) -> None:
        self._base.server.base_url = self._url_edit.text().strip()
        self._base.push.enabled = self._push_enabled.isChecked()
        self._base.push.interval_seconds = self._interval_spin.value()
        self._base.privacy.collect_screenshot = self._collect_screenshot.isChecked()
        self._base.privacy.collect_media = self._collect_media.isChecked()
        self._base.privacy.collect_processes = self._collect_processes.isChecked()
        self._base.privacy.collect_system_load = self._collect_system.isChecked()
        self._base.screenshot.blur_radius = self._blur_spin.value()
        self._base.screenshot.scale = self._scale_spin.value()
        self._base.screenshot.quality = self._quality_spin.value()
        self._base.process_whitelist = self._parse_whitelist(self._whitelist_edit.text())
        self._base.autostart.enabled = self._autostart_check.isChecked()
        self._base.ui.start_minimized = self._start_minimized.isChecked()

    def _parse_whitelist(self, text: str) -> list[str]:
        parts = [item.strip() for item in text.replace(",", "\n").splitlines()]
        return [item for item in parts if item]

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(self._build_server_group())
        root.addWidget(self._build_push_group())
        root.addWidget(self._build_privacy_group())
        root.addWidget(self._build_screenshot_group())
        root.addWidget(self._build_general_group())
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self._save_button)
        buttons.addWidget(self._cancel_button)
        root.addLayout(buttons)

    def _build_server_group(self) -> QGroupBox:
        group = QGroupBox("Server")
        form = QFormLayout(group)
        form.addRow("Base URL", self._url_edit)
        form.addRow("API Key", self._api_key_edit)
        return group

    def _build_push_group(self) -> QGroupBox:
        group = QGroupBox("Push")
        form = QFormLayout(group)
        form.addRow(self._push_enabled)
        form.addRow("Interval (s)", self._interval_spin)
        return group

    def _build_privacy_group(self) -> QGroupBox:
        group = QGroupBox("Privacy")
        form = QFormLayout(group)
        form.addRow(self._collect_screenshot)
        form.addRow(self._collect_media)
        form.addRow(self._collect_processes)
        form.addRow(self._collect_system)
        return group

    def _build_screenshot_group(self) -> QGroupBox:
        group = QGroupBox("Screenshot")
        form = QFormLayout(group)
        form.addRow("Blur radius", self._blur_spin)
        form.addRow("Scale", self._scale_spin)
        form.addRow("Quality", self._quality_spin)
        return group

    def _build_general_group(self) -> QGroupBox:
        group = QGroupBox("General")
        form = QFormLayout(group)
        form.addRow("Process whitelist", self._whitelist_edit)
        form.addRow(self._autostart_check)
        form.addRow(self._start_minimized)
        return group
