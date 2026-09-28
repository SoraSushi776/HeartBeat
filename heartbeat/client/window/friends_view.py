"""Friend link list and form backed by the v1 friends API."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.i18n import Translator


class FriendsView(QWidget):
    """List, create, edit, and delete friend links."""

    load_requested = Signal()
    create_requested = Signal(object)
    update_requested = Signal(int, object)
    delete_requested = Signal(int)

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self._current_id: int | None = None
        self._items: list[dict[str, Any]] = []
        self._list = QListWidget()
        self._name_edit = QLineEdit()
        self._url_edit = QLineEdit()
        self._avatar_edit = QLineEdit()
        self._description_edit = QLineEdit()
        self._sort_spin = QSpinBox()
        self._sort_spin.setRange(0, 9999)
        self._new_button = QPushButton()
        self._delete_button = QPushButton()
        self._save_button = QPushButton()
        self._name_label = QLabel()
        self._url_label = QLabel()
        self._avatar_label = QLabel()
        self._description_label = QLabel()
        self._sort_label = QLabel()
        self._build_layout()
        self.retranslate()
        self._wire()

    def apply_friends(self, data: object) -> None:
        """Fill the list from a friend list API payload."""
        rows = data if isinstance(data, list) else []
        self._items = [item for item in rows if isinstance(item, dict)]
        self._list.clear()
        if not self._items:
            self._list.addItem(self._t.tr("friend.empty_list"))
            return
        for item in self._items:
            entry = QListWidgetItem(str(item.get("name", "")))
            entry.setData(Qt.ItemDataRole.UserRole, item.get("id"))
            self._list.addItem(entry)
        self._list.setCurrentRow(0)

    def apply_friend_saved(self, data: object) -> None:
        """Store the saved row id and reload the list."""
        row = data if isinstance(data, dict) else {}
        saved_id = row.get("id")
        self._current_id = int(saved_id) if isinstance(saved_id, int) else None
        self.load_requested.emit()

    def apply_friend_deleted(self, friend_id: int) -> None:
        """Clear the form after a delete and reload the list."""
        if self._current_id == friend_id:
            self._clear_form()
        self.load_requested.emit()

    def show_error(self, message: str) -> None:
        """Surface an API failure to the user."""
        QMessageBox.warning(self, self._t.tr("error.title"), message)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._new_button.setText(self._t.tr("friend.new"))
        self._delete_button.setText(self._t.tr("friend.delete"))
        self._save_button.setText(self._t.tr("button.save"))
        self._name_label.setText(self._t.tr("friend.name"))
        self._url_label.setText(self._t.tr("friend.url"))
        self._avatar_label.setText(self._t.tr("friend.avatar"))
        self._description_label.setText(self._t.tr("friend.description"))
        self._sort_label.setText(self._t.tr("friend.sort"))

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.addWidget(self._new_button)
        toolbar.addWidget(self._delete_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self._save_button)
        form = QFormLayout()
        form.addRow(self._name_label, self._name_edit)
        form.addRow(self._url_label, self._url_edit)
        form.addRow(self._avatar_label, self._avatar_edit)
        form.addRow(self._description_label, self._description_edit)
        form.addRow(self._sort_label, self._sort_spin)
        right = QVBoxLayout()
        right.addLayout(form)
        right.addStretch(1)
        right_widget = QWidget()
        right_widget.setLayout(right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._list)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root = QVBoxLayout(self)
        root.addLayout(toolbar)
        root.addWidget(splitter, 1)

    def _wire(self) -> None:
        self._new_button.clicked.connect(self._on_new)
        self._delete_button.clicked.connect(self._on_delete)
        self._save_button.clicked.connect(self._on_save)
        self._list.currentItemChanged.connect(self._on_select)

    def _on_new(self) -> None:
        self._clear_form()

    def _on_delete(self) -> None:
        if self._current_id is None:
            return
        answer = QMessageBox.question(
            self,
            self._t.tr("friend.delete_confirm_title"),
            self._t.tr("friend.delete_confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.delete_requested.emit(self._current_id)

    def _on_save(self) -> None:
        payload = self._form_payload()
        if self._current_id is None:
            self.create_requested.emit(payload)
            return
        self.update_requested.emit(self._current_id, payload)

    def _on_select(
        self, current: QListWidgetItem | None, _prev: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        entry_id = current.data(Qt.ItemDataRole.UserRole)
        if entry_id is None:
            return
        row = self._find_item(int(entry_id))
        if row is None:
            return
        self._current_id = int(entry_id)
        self._name_edit.setText(str(row.get("name", "")))
        self._url_edit.setText(str(row.get("url", "")))
        self._avatar_edit.setText(str(row.get("avatar_url") or ""))
        self._description_edit.setText(str(row.get("description") or ""))
        sort_value = row.get("sort")
        self._sort_spin.setValue(int(sort_value) if isinstance(sort_value, int) else 0)

    def _find_item(self, friend_id: int) -> dict[str, Any] | None:
        for item in self._items:
            if item.get("id") == friend_id:
                return item
        return None

    def _clear_form(self) -> None:
        self._current_id = None
        self._name_edit.clear()
        self._url_edit.clear()
        self._avatar_edit.clear()
        self._description_edit.clear()
        self._sort_spin.setValue(0)

    def _form_payload(self) -> dict[str, Any]:
        return {
            "name": self._name_edit.text().strip(),
            "url": self._url_edit.text().strip(),
            "avatar_url": self._avatar_edit.text().strip() or None,
            "description": self._description_edit.text().strip() or None,
            "sort": self._sort_spin.value(),
        }
