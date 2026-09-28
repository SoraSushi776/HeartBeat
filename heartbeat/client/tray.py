from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from heartbeat.client.i18n import Translator

logger = logging.getLogger(__name__)

_IS_MACOS = sys.platform == "darwin"


def create_tray_icon() -> QIcon:
    """Build a mask-friendly tray icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setBrush(QColor(70, 130, 240))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(8, 8, 48, 48)
    painter.end()
    icon = QIcon(pixmap)
    icon.setIsMask(True)
    return icon


class TrayController(QObject):
    """System tray icon: left click restores the window, right click opens the menu."""

    def __init__(
        self,
        on_open: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        super().__init__()
        self._on_open = on_open
        self._on_quit = on_quit
        self._translator = Translator()
        self._icon = QSystemTrayIcon(create_tray_icon())
        self._icon.setToolTip("HeartBeat")
        self._menu = QMenu()
        self._open_action = QAction()
        self._quit_action = QAction()
        self._menu.addAction(self._open_action)
        self._menu.addAction(self._quit_action)
        self._open_action.triggered.connect(self._handle_open)
        self._quit_action.triggered.connect(self._handle_quit)
        self._icon.activated.connect(self._handle_activated)
        if not _IS_MACOS:
            self._icon.setContextMenu(self._menu)
        self.retranslate(self._translator.language)

    def retranslate(self, language: str) -> None:
        """Refresh tray menu labels for the active language."""
        self._translator.set_language(language)
        self._open_action.setText(self._translator.tr("menu.open"))
        self._quit_action.setText(self._translator.tr("menu.quit"))

    def show(self) -> None:
        """Show the tray icon."""
        self._icon.show()
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray unavailable on this desktop")

    def hide(self) -> None:
        """Hide the tray icon."""
        self._icon.hide()

    def notify(self, title: str, message: str) -> None:
        """Show a tray notification bubble."""
        self._icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information)

    def _handle_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        restore = {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.MiddleClick,
        }
        if reason in restore:
            self._handle_open()
            return
        if reason == QSystemTrayIcon.ActivationReason.Context and _IS_MACOS:
            self._popup_menu()

    def _popup_menu(self) -> None:
        self._menu.exec(QCursor.pos())

    def _handle_open(self) -> None:
        self._on_open()

    def _handle_quit(self) -> None:
        self._on_quit()
