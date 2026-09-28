"""Offscreen smoke checks for the guestbook client view and notify dispatch."""

from __future__ import annotations

import os
import unittest

from PySide6.QtWidgets import QApplication

from heartbeat.client import notify
from heartbeat.client.i18n import Translator
from heartbeat.client.window.message_view import MessageView
from heartbeat.client.worker.messages import _new_rows, _rows
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

    def test_main_window_includes_message_page(self) -> None:
        app = _app()
        from heartbeat.client.window.main_window import MainWindow

        window = MainWindow(Translator("zh-CN"))
        self.assertEqual(window._nav.count(), 5)
        self.assertIsNotNone(window.messages)
        window.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
