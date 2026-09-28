from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.config.models import AppConfig
from heartbeat.client.i18n import Translator


class SettingsView(QWidget):
    """Settings form assembled in code and driven entirely by config fields."""

    save_requested = Signal(object, str, str, str)
    background_requested = Signal()
    close_requested = Signal()

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self._base: AppConfig = AppConfig()
        self._url_edit = QLineEdit()
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._github_token_edit = QLineEdit()
        self._github_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._github_login_edit = QLineEdit()
        self._push_enabled = QCheckBox()
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(5, 3600)
        self._collect_screenshot = QCheckBox()
        self._collect_media = QCheckBox()
        self._collect_processes = QCheckBox()
        self._collect_system = QCheckBox()
        self._blur_spin = QDoubleSpinBox()
        self._blur_spin.setRange(0.0, 100.0)
        self._blur_spin.setSingleStep(0.5)
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.05, 1.0)
        self._scale_spin.setSingleStep(0.05)
        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(1, 100)
        self._autostart_check = QCheckBox()
        self._start_minimized = QCheckBox()
        self._site_title_edit = QLineEdit()
        self._site_tagline_edit = QLineEdit()
        self._site_process_title_edit = QLineEdit()
        self._site_tags_title_edit = QLineEdit()
        self._site_tags_edit = QLineEdit()
        self._site_show_heatmap = QCheckBox()
        self._save_button = QPushButton()
        self._cancel_button = QPushButton()
        self._background_button = QPushButton()
        self._server_group = QGroupBox()
        self._push_group = QGroupBox()
        self._privacy_group = QGroupBox()
        self._screenshot_group = QGroupBox()
        self._site_group = QGroupBox()
        self._general_group = QGroupBox()
        self._url_label = QLabel()
        self._api_key_label = QLabel()
        self._github_token_label = QLabel()
        self._github_login_label = QLabel()
        self._interval_label = QLabel()
        self._blur_label = QLabel()
        self._scale_label = QLabel()
        self._quality_label = QLabel()
        self._site_title_label = QLabel()
        self._site_tagline_label = QLabel()
        self._site_process_title_label = QLabel()
        self._site_tags_title_label = QLabel()
        self._site_tags_label = QLabel()
        self._build_layout()
        self.retranslate()
        self._save_button.clicked.connect(self._on_save)
        self._cancel_button.clicked.connect(self.close_requested.emit)
        self._background_button.clicked.connect(self.background_requested.emit)

    def apply_config(
        self,
        config: AppConfig,
        api_key: str,
        github_token: str = "",
        github_login: str = "",
    ) -> None:
        """Load config values into the form widgets."""
        self._base = config
        self._url_edit.setText(config.server.base_url)
        self._api_key_edit.setText(api_key)
        self._github_token_edit.setText(github_token)
        self._github_login_edit.setText(github_login)
        self._push_enabled.setChecked(config.push.enabled)
        self._interval_spin.setValue(config.push.interval_seconds)
        self._collect_screenshot.setChecked(config.privacy.collect_screenshot)
        self._collect_media.setChecked(config.privacy.collect_media)
        self._collect_processes.setChecked(config.privacy.collect_processes)
        self._collect_system.setChecked(config.privacy.collect_system_load)
        self._blur_spin.setValue(config.screenshot.blur_radius)
        self._scale_spin.setValue(config.screenshot.scale)
        self._quality_spin.setValue(config.screenshot.quality)
        self._autostart_check.setChecked(config.autostart.enabled)
        self._start_minimized.setChecked(config.ui.start_minimized)
        self._site_title_edit.setText(config.site.title)
        self._site_tagline_edit.setText(config.site.tagline)
        self._site_process_title_edit.setText(config.site.process_title)
        self._site_tags_title_edit.setText(config.site.tags_title)
        self._site_tags_edit.setText(", ".join(config.site.tags))
        self._site_show_heatmap.setChecked(config.site.show_heatmap)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._server_group.setTitle(self._t.tr("settings.server"))
        self._push_group.setTitle(self._t.tr("settings.push"))
        self._privacy_group.setTitle(self._t.tr("settings.privacy"))
        self._screenshot_group.setTitle(self._t.tr("settings.screenshot"))
        self._site_group.setTitle(self._t.tr("settings.site"))
        self._general_group.setTitle(self._t.tr("settings.general"))
        self._url_label.setText(self._t.tr("settings.base_url"))
        self._api_key_label.setText(self._t.tr("settings.api_key"))
        self._github_token_label.setText(self._t.tr("settings.github_token"))
        self._github_login_label.setText(self._t.tr("settings.github_login"))
        self._interval_label.setText(self._t.tr("settings.interval"))
        self._blur_label.setText(self._t.tr("settings.blur_radius"))
        self._scale_label.setText(self._t.tr("settings.scale"))
        self._quality_label.setText(self._t.tr("settings.quality"))
        self._site_title_label.setText(self._t.tr("settings.site_title"))
        self._site_tagline_label.setText(self._t.tr("settings.site_tagline"))
        self._site_process_title_label.setText(self._t.tr("settings.site_process_title"))
        self._site_tags_title_label.setText(self._t.tr("settings.site_tags_title"))
        self._site_tags_label.setText(self._t.tr("settings.site_tags"))
        self._site_show_heatmap.setText(self._t.tr("settings.site_show_heatmap"))
        self._push_enabled.setText(self._t.tr("settings.enable_push"))
        self._collect_screenshot.setText(self._t.tr("settings.collect_screenshot"))
        self._collect_media.setText(self._t.tr("settings.collect_media"))
        self._collect_processes.setText(self._t.tr("settings.collect_processes"))
        self._collect_system.setText(self._t.tr("settings.collect_system"))
        self._autostart_check.setText(self._t.tr("settings.autostart"))
        self._start_minimized.setText(self._t.tr("settings.start_minimized"))
        self._save_button.setText(self._t.tr("button.save"))
        self._cancel_button.setText(self._t.tr("button.close"))
        self._background_button.setText(self._t.tr("settings.upload_background"))

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
        github_token = self._github_token_edit.text().strip()
        github_login = self._github_login_edit.text().strip()
        self.save_requested.emit(self._base, api_key, github_token, github_login)

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
        self._base.autostart.enabled = self._autostart_check.isChecked()
        self._base.ui.start_minimized = self._start_minimized.isChecked()
        self._base.site.title = self._site_title_edit.text().strip() or self._base.site.title
        self._base.site.tagline = self._site_tagline_edit.text().strip()
        self._base.site.process_title = (
            self._site_process_title_edit.text().strip() or self._base.site.process_title
        )
        self._base.site.tags_title = (
            self._site_tags_title_edit.text().strip() or self._base.site.tags_title
        )
        self._base.site.tags = self._parse_whitelist(self._site_tags_edit.text())
        self._base.site.show_heatmap = self._site_show_heatmap.isChecked()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(self._build_server_group())
        root.addWidget(self._build_push_group())
        root.addWidget(self._build_privacy_group())
        root.addWidget(self._build_screenshot_group())
        root.addWidget(self._build_site_group())
        root.addWidget(self._build_general_group())
        buttons = QHBoxLayout()
        buttons.addWidget(self._background_button)
        buttons.addStretch(1)
        buttons.addWidget(self._save_button)
        buttons.addWidget(self._cancel_button)
        root.addLayout(buttons)

    def _build_server_group(self) -> QGroupBox:
        form = QFormLayout(self._server_group)
        form.addRow(self._url_label, self._url_edit)
        form.addRow(self._api_key_label, self._api_key_edit)
        form.addRow(self._github_token_label, self._github_token_edit)
        form.addRow(self._github_login_label, self._github_login_edit)
        return self._server_group

    def _build_push_group(self) -> QGroupBox:
        form = QFormLayout(self._push_group)
        form.addRow(self._push_enabled)
        form.addRow(self._interval_label, self._interval_spin)
        return self._push_group

    def _build_privacy_group(self) -> QGroupBox:
        form = QFormLayout(self._privacy_group)
        form.addRow(self._collect_screenshot)
        form.addRow(self._collect_media)
        form.addRow(self._collect_processes)
        form.addRow(self._collect_system)
        return self._privacy_group

    def _build_screenshot_group(self) -> QGroupBox:
        form = QFormLayout(self._screenshot_group)
        form.addRow(self._blur_label, self._blur_spin)
        form.addRow(self._scale_label, self._scale_spin)
        form.addRow(self._quality_label, self._quality_spin)
        return self._screenshot_group

    def _build_site_group(self) -> QGroupBox:
        form = QFormLayout(self._site_group)
        form.addRow(self._site_title_label, self._site_title_edit)
        form.addRow(self._site_tagline_label, self._site_tagline_edit)
        form.addRow(self._site_process_title_label, self._site_process_title_edit)
        form.addRow(self._site_tags_title_label, self._site_tags_title_edit)
        form.addRow(self._site_tags_label, self._site_tags_edit)
        form.addRow(self._site_show_heatmap)
        return self._site_group

    def _parse_whitelist(self, text: str) -> list[str]:
        parts = [item.strip() for item in text.replace(",", "\n").splitlines()]
        return [item for item in parts if item]

    def _build_general_group(self) -> QGroupBox:
        form = QFormLayout(self._general_group)
        form.addRow(self._autostart_check)
        form.addRow(self._start_minimized)
        return self._general_group
