"""Diary list and Markdown editor backed by the v1 diary API."""

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
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.i18n import Translator
from heartbeat.client.markdown import markdown_to_html


class DiaryView(QWidget):
    """List, create, edit, and delete diary entries."""

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
        self._title_edit = QLineEdit()
        self._mood_edit = QLineEdit()
        self._tags_edit = QLineEdit()
        self._content_edit = QPlainTextEdit()
        self._preview = QTextBrowser()
        self._new_button = QPushButton()
        self._delete_button = QPushButton()
        self._save_button = QPushButton()
        self._preview_button = QPushButton()
        self._title_label = QLabel()
        self._mood_label = QLabel()
        self._tags_label = QLabel()
        self._content_label = QLabel()
        self._preview_visible = False
        self._build_layout()
        self.retranslate()
        self._wire()

    def apply_diaries(self, data: object) -> None:
        """Fill the list from a diary list API payload."""
        payload = data if isinstance(data, dict) else {}
        items = payload.get("items")
        if isinstance(items, list):
            self._items = [item for item in items if isinstance(item, dict)]
        else:
            self._items = []
        self._list.clear()
        if not self._items:
            self._list.addItem(self._t.tr("diary.empty_list"))
            return
        for item in self._items:
            entry = QListWidgetItem(str(item.get("title", "")))
            entry.setData(Qt.ItemDataRole.UserRole, item.get("id"))
            self._list.addItem(entry)
        self._list.setCurrentRow(0)

    def apply_diary_saved(self, data: object) -> None:
        """Store the saved row id and reload the list."""
        row = data if isinstance(data, dict) else {}
        saved_id = row.get("id")
        self._current_id = int(saved_id) if isinstance(saved_id, int) else None
        self.load_requested.emit()

    def apply_diary_deleted(self, diary_id: int) -> None:
        """Clear the form after a delete and reload the list."""
        if self._current_id == diary_id:
            self._clear_form()
        self.load_requested.emit()

    def show_error(self, message: str) -> None:
        """Surface an API failure to the user."""
        QMessageBox.warning(self, self._t.tr("error.title"), message)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._new_button.setText(self._t.tr("diary.new"))
        self._delete_button.setText(self._t.tr("diary.delete"))
        self._save_button.setText(self._t.tr("button.save"))
        self._preview_button.setText(self._t.tr("button.preview"))
        self._title_label.setText(self._t.tr("diary.title"))
        self._mood_label.setText(self._t.tr("diary.mood"))
        self._tags_label.setText(self._t.tr("diary.tags"))
        self._content_label.setText(self._t.tr("diary.content"))
        self._tags_edit.setPlaceholderText(self._t.tr("diary.tags_placeholder"))

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.addWidget(self._new_button)
        toolbar.addWidget(self._delete_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self._preview_button)
        toolbar.addWidget(self._save_button)
        form = QFormLayout()
        form.addRow(self._title_label, self._title_edit)
        form.addRow(self._mood_label, self._mood_edit)
        form.addRow(self._tags_label, self._tags_edit)
        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(self._content_label)
        right.addWidget(self._content_edit, 1)
        right.addWidget(self._preview, 1)
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
        self._preview.hide()

    def _wire(self) -> None:
        self._new_button.clicked.connect(self._on_new)
        self._delete_button.clicked.connect(self._on_delete)
        self._save_button.clicked.connect(self._on_save)
        self._preview_button.clicked.connect(self._on_toggle_preview)
        self._list.currentItemChanged.connect(self._on_select)

    def _on_new(self) -> None:
        self._clear_form()

    def _on_delete(self) -> None:
        if self._current_id is None:
            return
        answer = QMessageBox.question(
            self,
            self._t.tr("diary.delete_confirm_title"),
            self._t.tr("diary.delete_confirm_text"),
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

    def _on_toggle_preview(self) -> None:
        self._preview_visible = not self._preview_visible
        self._content_edit.setVisible(not self._preview_visible)
        self._preview.setVisible(self._preview_visible)
        if self._preview_visible:
            self._preview.setHtml(markdown_to_html(self._content_edit.toPlainText()))

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
        self._title_edit.setText(str(row.get("title", "")))
        self._mood_edit.setText(str(row.get("mood") or ""))
        self._tags_edit.setText(", ".join(str(tag) for tag in row.get("tags") or []))
        self._content_edit.setPlainText(str(row.get("content", "")))
        self._preview.setHtml(markdown_to_html(str(row.get("content", ""))))

    def _find_item(self, diary_id: int) -> dict[str, Any] | None:
        for item in self._items:
            if item.get("id") == diary_id:
                return item
        return None

    def _clear_form(self) -> None:
        self._current_id = None
        self._title_edit.clear()
        self._mood_edit.clear()
        self._tags_edit.clear()
        self._content_edit.clear()
        self._preview.clear()

    def _form_payload(self) -> dict[str, Any]:
        tags = [item.strip() for item in self._tags_edit.text().replace(",", "\n").splitlines()]
        return {
            "title": self._title_edit.text().strip(),
            "content": self._content_edit.toPlainText(),
            "mood": self._mood_edit.text().strip() or None,
            "tags": [tag for tag in tags if tag],
        }
