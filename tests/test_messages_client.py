"""Offscreen smoke checks for the guestbook client view and notify dispatch."""

from __future__ import annotations

import os
import unittest

from PySide6.QtWidgets import QApplication, QMessageBox

from heartbeat.client import notify
from heartbeat.client.api import ApiError
from heartbeat.client.i18n import Translator
from heartbeat.client.window.message_view import MessageView
from heartbeat.client.window.reply_dialog import REPLY_MAX_LENGTH, ReplyDialog
from heartbeat.client.worker.messages import MessageWorker, _new_rows, _rows
from heartbeat.protocol.models import Platform

_APP: QApplication | None = None


def _app() -> QApplication:
    global _APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class NotifyCommandTest(unittest.TestCase):
    def test_macos_command_quotes_payload(self) -> None:
        command = notify.macos_command('Hi "there"', "line\\two")
        self.assertEqual(command[0], "osascript")
        self.assertIn('display notification', command[2])
        self.assertIn('\\"there\\"', command[2])
        self.assertIn("\\\\two", command[2])

    def test_windows_command_is_powershell_toast(self) -> None:
        command = notify.windows_command("T", "M")
        self.assertEqual(command[0], "powershell")
        self.assertIn("ToastNotification", command[-1])
        self.assertIn("ToastText02", command[-1])

    def test_linux_command_uses_notify_send(self) -> None:
        command = notify.linux_command("T", "M")
        self.assertEqual(command[0], "notify-send")
        self.assertEqual(command[-2:], ["T", "M"])

    def test_dispatch_table_covers_every_platform(self) -> None:
        self.assertEqual(set(notify._COMMANDS), set(Platform))


class MessageRowsTest(unittest.TestCase):
    def test_rows_extracts_items(self) -> None:
        rows = _rows({"items": [{"id": 1}, "bad", {"id": 2}]})
        self.assertEqual([row["id"] for row in rows], [1, 2])
        self.assertEqual(_rows(None), [])

    def test_new_rows_silent_until_primed(self) -> None:
        rows = [{"id": 1, "created_ts": 10}]
        self.assertEqual(_new_rows(rows, set(), False), [])

    def test_new_rows_reports_unseen_in_chronological_order(self) -> None:
        rows = [
            {"id": 3, "created_ts": 30},
            {"id": 2, "created_ts": 20},
            {"id": 1, "created_ts": 10},
        ]
        fresh = _new_rows(rows, {1}, True)
        self.assertEqual([row["id"] for row in fresh], [2, 3])


class MessageViewTest(unittest.TestCase):
    def test_construct_apply_and_retranslate(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages(
            {
                "items": [
                    {"id": 1, "author": "Sora", "content": "hello", "created_ts": 1},
                    {"id": 2, "author": "", "content": "anon", "created_ts": 2},
                ]
            }
        )
        self.assertEqual(view._list.count(), 2)
        self.assertIn("匿名", view._list.item(1).text())
        view.apply_messages({"items": []})
        self.assertEqual(view._list.count(), 0)
        self.assertFalse(view._empty_label.isHidden())
        view.retranslate()
        view.close()
        app.processEvents()

    def test_apply_messages_shows_ip_and_location(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages(
            {
                "items": [
                    {
                        "id": 7,
                        "author": "Sora",
                        "content": "hi",
                        "created_ts": 1,
                        "ip": "203.0.113.9",
                        "location": "广东",
                    }
                ]
            }
        )
        text = view._list.item(0).text()
        self.assertIn("203.0.113.9", text)
        self.assertIn("广东", text)
        self.assertIn("hi", text)
        view.close()
        app.processEvents()

    def test_apply_messages_marks_unknown_ip_and_location(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages({"items": [{"id": 1, "author": "", "content": "x", "created_ts": 1}]})
        text = view._list.item(0).text()
        self.assertIn("未知 IP", text)
        self.assertIn("未知", text)
        view.close()
        app.processEvents()

    def test_delete_signal_carries_message_id(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages({"items": [{"id": 42, "author": "a", "content": "b", "created_ts": 1}]})
        received: list[int] = []
        view.delete_requested.connect(received.append)
        view._list.setCurrentRow(0)
        original = QMessageBox.question
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        try:
            view._on_delete()
        finally:
            QMessageBox.question = original
        self.assertEqual(received, [42])
        view.close()
        app.processEvents()

    def test_ban_signal_carries_ip(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages(
            {
                "items": [
                    {"id": 1, "author": "a", "content": "b", "created_ts": 1, "ip": "198.51.100.4"}
                ]
            }
        )
        received: list[str] = []
        view.ban_requested.connect(received.append)
        view._list.setCurrentRow(0)
        original = QMessageBox.question
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        try:
            view._on_ban()
        finally:
            QMessageBox.question = original
        self.assertEqual(received, ["198.51.100.4"])
        view.close()
        app.processEvents()

    def test_unban_signal_carries_ban_id(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_bans({"items": [{"id": 9, "ip": "10.0.0.1", "created_ts": 1}]})
        received: list[int] = []
        view.unban_requested.connect(received.append)
        view._ban_list.setCurrentRow(0)
        view._on_unban()
        self.assertEqual(received, [9])
        view.close()
        app.processEvents()

    def test_apply_bans_fills_list(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_bans({"items": [{"id": 1, "ip": "1.2.3.4", "created_ts": 1}]})
        self.assertEqual(view._ban_list.count(), 1)
        self.assertEqual(view._ban_list.item(0).text(), "1.2.3.4")
        view.apply_bans({"items": []})
        self.assertEqual(view._ban_list.count(), 0)
        self.assertFalse(view._ban_empty_label.isHidden())
        view.close()
        app.processEvents()

    def test_main_window_includes_message_page(self) -> None:
        app = _app()
        from heartbeat.client.window.main_window import MainWindow

        window = MainWindow(Translator("zh-CN"))
        self.assertEqual(window._nav.count(), 5)
        self.assertIsNotNone(window.messages)
        window.close()
        app.processEvents()


class MessageReplyTest(unittest.TestCase):
    def test_row_text_marks_reply_count_and_tooltip(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages(
            {
                "items": [
                    {
                        "id": 1,
                        "author": "Sora",
                        "content": "hi",
                        "created_ts": 1,
                        "replies": [{"id": 5, "content": "welcome", "created_ts": 2}],
                    },
                    {"id": 2, "author": "", "content": "plain", "created_ts": 3},
                ]
            }
        )
        self.assertIn("1 条回复", view._list.item(0).text())
        self.assertIn("welcome", view._list.item(0).toolTip())
        self.assertNotIn("条回复", view._list.item(1).text())
        view.close()
        app.processEvents()

    def test_row_text_survives_missing_replies(self) -> None:
        app = _app()
        view = MessageView(Translator("zh-CN"))
        view.apply_messages(
            {"items": [{"id": 1, "content": "x", "created_ts": 1, "replies": None}]}
        )
        self.assertNotIn("条回复", view._list.item(0).text())
        view.retranslate()
        view.close()
        app.processEvents()

    def test_reply_dialog_gates_submit_on_content(self) -> None:
        app = _app()
        dialog = ReplyDialog(
            Translator("zh-CN"),
            {
                "id": 1,
                "author": "Sora",
                "content": "hi",
                "replies": [{"id": 5, "content": "welcome"}],
            },
        )
        self.assertFalse(dialog._ok_button.isEnabled())
        self.assertEqual(dialog._replies.count(), 1)
        dialog._content.setPlainText("  answer  ")
        self.assertTrue(dialog._ok_button.isEnabled())
        self.assertEqual(dialog.reply_text(), "answer")
        dialog._content.setPlainText("   ")
        self.assertFalse(dialog._ok_button.isEnabled())
        dialog.close()
        app.processEvents()

    def test_reply_dialog_without_replies_hides_list(self) -> None:
        app = _app()
        dialog = ReplyDialog(Translator("zh-CN"), {"id": 1, "author": "", "content": "hi"})
        self.assertFalse(dialog._replies.isVisibleTo(dialog))
        self.assertTrue(dialog._replies_empty_label.isVisibleTo(dialog))
        dialog.close()
        app.processEvents()

    def test_reply_dialog_caps_length(self) -> None:
        app = _app()
        dialog = ReplyDialog(Translator("zh-CN"), {"id": 1, "content": "hi"})
        dialog._content.setPlainText("x" * (REPLY_MAX_LENGTH + 40))
        self.assertEqual(len(dialog._content.toPlainText()), REPLY_MAX_LENGTH)
        dialog.close()
        app.processEvents()

    def test_worker_reports_created_reply(self) -> None:
        service = _StubService(result={"id": 7, "message_id": 2, "content": "ok"})
        worker = MessageWorker(service)
        created: list[object] = []
        worker.reply_created.connect(created.append)
        worker.create_reply(2, "ok")
        self.assertEqual(created, [{"id": 7, "message_id": 2, "content": "ok"}])

    def test_worker_reports_reply_failure(self) -> None:
        service = _StubService(failure=ApiError("boom"))
        worker = MessageWorker(service)
        failures: list[str] = []
        worker.reply_create_failed.connect(failures.append)
        worker.create_reply(2, "ok")
        self.assertEqual(failures, ["boom"])


class _StubService:
    """ApiService stand-in recording reply calls."""

    def __init__(self, result: object = None, failure: Exception | None = None) -> None:
        self._result = result
        self._failure = failure
        self.calls: list[tuple[int, str]] = []

    def create_message_reply(self, message_id: int, content: str) -> object:
        self.calls.append((message_id, content))
        if self._failure is not None:
            raise self._failure
        return self._result


if __name__ == "__main__":
    unittest.main()
