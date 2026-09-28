"""Wide main window with navigation rail and stacked content panels."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from heartbeat.client.config.models import AppConfig
from heartbeat.client.diagnostics import DiagnosticsSnapshot
from heartbeat.client.i18n import Translator
from heartbeat.client.window.diagnostics_view import DiagnosticsView
from heartbeat.client.window.diary_view import DiaryView
from heartbeat.client.window.friends_view import FriendsView
from heartbeat.client.window.message_view import MessageView
from heartbeat.client.window.settings_view import SettingsView

MAIN_WINDOW_WIDTH = 960
MAIN_WINDOW_HEIGHT = 640
NAV_WIDTH = 160
NAV_KEYS: tuple[str, ...] = (
    "nav.settings",
    "nav.diagnostics",
    "nav.diaries",
    "nav.friends",
    "nav.messages",
)
LANGUAGE_CODES: tuple[str, ...] = ("zh-CN", "en-US")
LANGUAGE_LABELS: tuple[str, ...] = ("中文", "English")


class MainWindow(QMainWindow):
    """Host settings, diagnostics, diary, and friend panels behind a nav rail."""

    save_requested = Signal(object, str, str, str)
    background_requested = Signal()
    close_requested = Signal()
    diagnostics_refresh_requested = Signal()
    display_list_changed = Signal(list)
    language_change_requested = Signal(str)
    page_changed = Signal(int)

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        self._nav = QListWidget()
        self._nav.setFixedWidth(NAV_WIDTH)
        self._stack = QStackedWidget()
        self._settings = SettingsView(translator)
        self._diagnostics = DiagnosticsView(translator)
        self._diary = DiaryView(translator)
        self._friends = FriendsView(translator)
        self._messages = MessageView(translator)
        self._language_menu = self.menuBar().addMenu("")
        self._language_actions: list = []
        self._build_layout()
        self._build_language_menu()
        self.retranslate()
        self._wire()

    @property
    def diary(self) -> DiaryView:
        return self._diary

    @property
    def friends(self) -> FriendsView:
        return self._friends

    @property
    def messages(self) -> MessageView:
        return self._messages

    @property
    def diagnostics(self) -> DiagnosticsView:
        return self._diagnostics

    @property
    def translator(self) -> Translator:
        return self._t

    def apply_config(
        self,
        config: AppConfig,
        api_key: str,
        github_token: str = "",
        github_login: str = "",
    ) -> None:
        """Load config values into the settings form."""
        self._settings.apply_config(config, api_key, github_token, github_login)

    def apply_diagnostics(self, snapshot: DiagnosticsSnapshot) -> None:
        """Push a live snapshot into the diagnostics panel."""
        self._diagnostics.apply_snapshot(snapshot)

    def record_push_success(self, ts: float) -> None:
        """Record a successful push in the diagnostics log."""
        self._diagnostics.record_push_success(ts)

    def record_push_failure(self, kind: str, attempt: int) -> None:
        """Record a failed push in the diagnostics log."""
        self._diagnostics.record_push_failure(kind, attempt)

    def set_language(self, language: str) -> None:
        """Switch the active language and refresh every panel."""
        self._t.set_language(language)
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self.setWindowTitle(self._t.tr("app.title"))
        self._language_menu.setTitle(self._t.tr("menu.language"))
        for index, key in enumerate(NAV_KEYS):
            item = self._nav.item(index)
            if item is not None:
                item.setText(self._t.tr(key))
        self._settings.retranslate()
        self._diagnostics.retranslate()
        self._diary.retranslate()
        self._friends.retranslate()
        self._messages.retranslate()

    def is_visible(self) -> bool:
        """Return whether the main window is currently shown."""
        return self.isVisible()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Hide the window instead of destroying it on close."""
        self.close_requested.emit()
        event.accept()

    def _build_layout(self) -> None:
        body = QWidget()
        row = QHBoxLayout(body)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._nav)
        row.addWidget(self._stack, 1)
        self.setCentralWidget(body)
        self._stack.addWidget(self._settings)
        self._stack.addWidget(self._diagnostics)
        self._stack.addWidget(self._diary)
        self._stack.addWidget(self._friends)
        self._stack.addWidget(self._messages)
        for key in NAV_KEYS:
            self._nav.addItem(QListWidgetItem(self._t.tr(key)))
        self._nav.setCurrentRow(0)

    def _build_language_menu(self) -> None:
        for code, label in zip(LANGUAGE_CODES, LANGUAGE_LABELS, strict=True):
            action = self._language_menu.addAction(label)
            action.triggered.connect(self._make_language_handler(code))
            self._language_actions.append(action)

    def _make_language_handler(self, code: str):
        def handler() -> None:
            self.language_change_requested.emit(code)

        return handler

    def _wire(self) -> None:
        self._nav.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._nav.currentRowChanged.connect(self.page_changed.emit)
        self._settings.save_requested.connect(self.save_requested.emit)
        self._settings.background_requested.connect(self.background_requested.emit)
        self._settings.close_requested.connect(self.close_requested.emit)
        self._diagnostics.refresh_requested.connect(self.diagnostics_refresh_requested.emit)
        self._diagnostics.display_list_changed.connect(self.display_list_changed.emit)
