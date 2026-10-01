"""Guestbook reply composer dialog."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from heartbeat.client.i18n import Translator

REPLY_MAX_LENGTH = 500
REPLY_DIALOG_WIDTH = 480
REPLY_DIALOG_HEIGHT = 440
REPLY_LIST_HEIGHT = 120


class ReplyDialog(QDialog):
    """Compose one guestbook reply and show the message with its existing replies."""

    def __init__(
        self,
        translator: Translator,
        row: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._t = translator
        self._original_label = QLabel()
        self._replies_title = QLabel()
        self._replies_empty_label = QLabel()
        self._content_label = QLabel()
        self._replies = QListWidget()
        self._content = QPlainTextEdit()
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)
        self._build_layout()
        self._apply_row(row)
        self.retranslate()
        self._wire()

    def reply_text(self) -> str:
        """Return the trimmed reply text typed by the user."""
        return self._content.toPlainText().strip()

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self.setWindowTitle(self._t.tr("message.reply_title"))
        self._replies_title.setText(self._t.tr("message.reply_existing"))
        self._replies_empty_label.setText(self._t.tr("message.reply_existing_empty"))
        self._content_label.setText(self._t.tr("message.reply_content"))
        self._content.setPlaceholderText(self._t.tr("message.reply_placeholder"))
        self._ok_button.setText(self._t.tr("message.reply_submit"))
        self._buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._t.tr("button.cancel")
        )

    def _build_layout(self) -> None:
        self._original_label.setWordWrap(True)
        self._replies_title.setVisible(False)
        self._replies.setVisible(False)
        self._replies.setFixedHeight(REPLY_LIST_HEIGHT)
        self._content.setFixedHeight(REPLY_LIST_HEIGHT)
        layout = QVBoxLayout(self)
        layout.addWidget(self._original_label)
        layout.addWidget(self._replies_title)
        layout.addWidget(self._replies_empty_label)
        layout.addWidget(self._replies)
        layout.addWidget(self._content_label)
        layout.addWidget(self._content)
        layout.addWidget(self._buttons)
        self.resize(REPLY_DIALOG_WIDTH, REPLY_DIALOG_HEIGHT)

    def _wire(self) -> None:
        self._content.textChanged.connect(self._on_text_changed)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

    def _apply_row(self, row: dict[str, Any]) -> None:
        author = str(row.get("author") or "").strip() or self._t.tr("message.anonymous")
        content = str(row.get("content") or "")
        self._original_label.setText(f"{author}\n{content}")
        replies = _reply_rows(row.get("replies"))
        has_replies = bool(replies)
        self._replies_title.setVisible(has_replies)
        self._replies.setVisible(has_replies)
        self._replies_empty_label.setVisible(not has_replies)
        for item in replies:
            self._replies.addItem(str(item.get("content") or ""))

    def _on_text_changed(self) -> None:
        """Cap the reply length and allow submitting only non-blank text."""
        text = self._content.toPlainText()
        if len(text) > REPLY_MAX_LENGTH:
            self._content.setPlainText(text[:REPLY_MAX_LENGTH])
            cursor = self._content.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._content.setTextCursor(cursor)
        self._ok_button.setEnabled(bool(self._content.toPlainText().strip()))


def _reply_rows(value: object) -> list[dict[str, Any]]:
    """Filter a reply payload list down to dict rows."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
