"""Guestbook message history list backed by the v1 message API."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.i18n import Translator


class MessageView(QWidget):
    """Show guestbook history with manual refresh."""

    load_requested = Signal()

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self._list = QListWidget()
        self._refresh_button = QPushButton()
        self._empty_label = QLabel()
        self._build_layout()
        self.retranslate()
        self._wire()

    def apply_messages(self, data: object) -> None:
        """Fill the list from a message list API payload."""
        payload = data if isinstance(data, dict) else {}
        items = payload.get("items")
        rows = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        self._list.clear()
        self._empty_label.setVisible(not rows)
        for row in rows:
            self._list.addItem(_to_item(row, self._t))

    def show_error(self, message: str) -> None:
        """Surface an API failure to the user."""
        QMessageBox.warning(self, self._t.tr("error.title"), message)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._refresh_button.setText(self._t.tr("button.refresh"))
        self._empty_label.setText(self._t.tr("message.empty_list"))

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.addWidget(self._empty_label)
        toolbar.addStretch(1)
        toolbar.addWidget(self._refresh_button)
        root = QVBoxLayout(self)
        root.addLayout(toolbar)
        root.addWidget(self._list, 1)

    def _wire(self) -> None:
        self._refresh_button.clicked.connect(self.load_requested.emit)


def _to_item(row: dict[str, Any], translator: Translator) -> QListWidgetItem:
    """Build one list entry from a message row."""
    author = str(row.get("author") or "").strip() or translator.tr("message.anonymous")
    content = str(row.get("content") or "")
    item = QListWidgetItem(f"{author}  ·  {content}")
    item.setToolTip(content)
    return item
