"""Guestbook admin view showing IP, location and ban management."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.i18n import Translator


class MessageView(QWidget):
    """Show guestbook rows with IP, location, delete and IP ban controls."""

    load_requested = Signal()
    bans_requested = Signal()
    delete_requested = Signal(int)
    ban_requested = Signal(str)
    unban_requested = Signal(int)

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self._rows: list[dict[str, Any]] = []
        self._bans: list[dict[str, Any]] = []
        self._list = QListWidget()
        self._ban_list = QListWidget()
        self._refresh_button = QPushButton()
        self._delete_button = QPushButton()
        self._ban_button = QPushButton()
        self._unban_button = QPushButton()
        self._empty_label = QLabel()
        self._ban_title = QLabel()
        self._ban_empty_label = QLabel()
        self._build_layout()
        self.retranslate()
        self._wire()

    def apply_messages(self, data: object) -> None:
        """Fill the message list from an admin message list payload."""
        payload = data if isinstance(data, dict) else {}
        items = payload.get("items")
        self._rows = _dict_rows(items)
        self._list.clear()
        self._empty_label.setVisible(not self._rows)
        for row in self._rows:
            self._list.addItem(_to_item(row, self._t))

    def apply_bans(self, data: object) -> None:
        """Fill the ban list from a ban list payload."""
        payload = data if isinstance(data, dict) else {}
        items = payload.get("items")
        self._bans = _dict_rows(items)
        self._ban_list.clear()
        self._ban_empty_label.setVisible(not self._bans)
        for row in self._bans:
            entry = QListWidgetItem(str(row.get("ip") or ""))
            entry.setData(Qt.ItemDataRole.UserRole, row.get("id"))
            self._ban_list.addItem(entry)

    def show_error(self, message: str) -> None:
        """Surface an API failure to the user."""
        QMessageBox.warning(self, self._t.tr("error.title"), message)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._refresh_button.setText(self._t.tr("button.refresh"))
        self._delete_button.setText(self._t.tr("button.delete"))
        self._ban_button.setText(self._t.tr("message.ban_ip"))
        self._unban_button.setText(self._t.tr("message.unban_ip"))
        self._empty_label.setText(self._t.tr("message.empty_list"))
        self._ban_title.setText(self._t.tr("message.ban_list"))
        self._ban_empty_label.setText(self._t.tr("message.ban_empty"))
        self._rebuild_texts()

    def _rebuild_texts(self) -> None:
        for index, row in enumerate(self._rows):
            item = self._list.item(index)
            if item is not None:
                item.setText(_row_text(row, self._t))

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.addWidget(self._empty_label)
        toolbar.addStretch(1)
        toolbar.addWidget(self._delete_button)
        toolbar.addWidget(self._ban_button)
        toolbar.addWidget(self._refresh_button)
        message_panel = QWidget()
        message_layout = QVBoxLayout(message_panel)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.addLayout(toolbar)
        message_layout.addWidget(self._list, 1)
        ban_toolbar = QHBoxLayout()
        ban_toolbar.addWidget(self._ban_title)
        ban_toolbar.addStretch(1)
        ban_toolbar.addWidget(self._ban_empty_label)
        ban_toolbar.addWidget(self._unban_button)
        ban_panel = QWidget()
        ban_layout = QVBoxLayout(ban_panel)
        ban_layout.setContentsMargins(0, 0, 0, 0)
        ban_layout.addLayout(ban_toolbar)
        ban_layout.addWidget(self._ban_list, 1)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(message_panel)
        splitter.addWidget(ban_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root = QVBoxLayout(self)
        root.addWidget(splitter, 1)

    def _wire(self) -> None:
        self._refresh_button.clicked.connect(self._on_refresh)
        self._delete_button.clicked.connect(self._on_delete)
        self._ban_button.clicked.connect(self._on_ban)
        self._unban_button.clicked.connect(self._on_unban)

    def _on_refresh(self) -> None:
        self.load_requested.emit()
        self.bans_requested.emit()

    def _on_delete(self) -> None:
        message_id = self._selected_message_id()
        if message_id is None:
            return
        answer = QMessageBox.question(
            self,
            self._t.tr("message.delete_confirm_title"),
            self._t.tr("message.delete_confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.delete_requested.emit(message_id)

    def _on_ban(self) -> None:
        ip = self._selected_ip()
        if not ip:
            return
        answer = QMessageBox.question(
            self,
            self._t.tr("message.ban_confirm_title"),
            self._t.tr("message.ban_confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.ban_requested.emit(ip)

    def _on_unban(self) -> None:
        ban_id = self._selected_ban_id()
        if ban_id is None:
            return
        self.unban_requested.emit(ban_id)

    def _selected_message_id(self) -> int | None:
        row = self._selected_row()
        if row is None:
            return None
        value = row.get("id")
        return int(value) if isinstance(value, int) else None

    def _selected_ip(self) -> str:
        row = self._selected_row()
        if row is None:
            return ""
        return str(row.get("ip") or "").strip()

    def _selected_row(self) -> dict[str, Any] | None:
        index = self._list.currentRow()
        if index < 0 or index >= len(self._rows):
            return None
        return self._rows[index]

    def _selected_ban_id(self) -> int | None:
        item = self._ban_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if isinstance(value, int) else None


def _dict_rows(items: object) -> list[dict[str, Any]]:
    """Filter a payload list down to dict rows."""
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _row_text(row: dict[str, Any], translator: Translator) -> str:
    """Build one display line from a message row."""
    author = str(row.get("author") or "").strip() or translator.tr("message.anonymous")
    content = str(row.get("content") or "")
    ip = str(row.get("ip") or "").strip() or translator.tr("message.unknown_ip")
    location = str(row.get("location") or "").strip() or translator.tr("message.unknown_location")
    return f"{author}  ·  {ip}  ·  {location}  ·  {content}"


def _to_item(row: dict[str, Any], translator: Translator) -> QListWidgetItem:
    """Build one list entry from a message row."""
    item = QListWidgetItem(_row_text(row, translator))
    item.setToolTip(str(row.get("content") or ""))
    return item
