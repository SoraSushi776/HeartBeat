"""Live diagnostics panel for music, processes, system load, and push results."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QHideEvent, QImage, QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from heartbeat.adapters.processes.collector import PsutilProcessAdapter
from heartbeat.adapters.processes.filter import ProcessFilter
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.client.diagnostics import DiagnosticsSnapshot, format_ms
from heartbeat.client.i18n import Translator
from heartbeat.protocol.models import Capability, MediaInfo, MediaState, ProcessInfo, SystemInfo

PUSH_LOG_LIMIT = 20
COVER_SIZE = 96
AUTO_REFRESH_MS = 5000


class DiagnosticsView(QWidget):
    """Show a live local snapshot and manage the process display list."""

    refresh_requested = Signal()
    display_list_changed = Signal(list)

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self._t = translator
        self._cover_label = QLabel()
        self._cover_label.setFixedSize(COVER_SIZE, COVER_SIZE)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label = QLabel()
        self._artist_label = QLabel()
        self._album_label = QLabel()
        self._progress_label = QLabel()
        self._process_list = QListWidget()
        self._display_list = QListWidget()
        self._cpu_label = QLabel()
        self._memory_label = QLabel()
        self._load_label = QLabel()
        self._push_log = QListWidget()
        self._refresh_button = QPushButton()
        self._add_display_button = QPushButton()
        self._remove_display_button = QPushButton()
        self._music_group = QGroupBox()
        self._processes_group = QGroupBox()
        self._display_group = QGroupBox()
        self._system_group = QGroupBox()
        self._push_group = QGroupBox()
        self._title_caption = QLabel()
        self._artist_caption = QLabel()
        self._album_caption = QLabel()
        self._progress_caption = QLabel()
        self._cpu_caption = QLabel()
        self._memory_caption = QLabel()
        self._load_caption = QLabel()
        self._display_names: list[str] = []
        self._timer = QTimer(self)
        self._timer.setInterval(AUTO_REFRESH_MS)
        self._timer.timeout.connect(self.refresh_requested.emit)
        self._build_layout()
        self.retranslate()
        self._refresh_button.clicked.connect(self.refresh_requested.emit)
        self._add_display_button.clicked.connect(self._add_selected_process)
        self._remove_display_button.clicked.connect(self._remove_selected_display)
        self._process_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._process_list.customContextMenuRequested.connect(self._show_process_menu)
        self._display_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._display_list.customContextMenuRequested.connect(self._show_display_menu)

    def apply_snapshot(self, snapshot: DiagnosticsSnapshot) -> None:
        """Render a fresh local collection result."""
        self._apply_media(snapshot.media, snapshot.cover_bytes)
        self._apply_processes(snapshot.processes)
        self._apply_system(snapshot.system)

    def set_display_list(self, names: list[str]) -> None:
        """Replace the process display list shown next to the process list."""
        self._display_names = list(dict.fromkeys(names))
        self._refresh_display_list()

    def display_list(self) -> list[str]:
        """Return the current process display list."""
        return list(self._display_names)

    def record_push_success(self, ts: float) -> None:
        """Append a push success entry to the recent log."""
        stamp = datetime.now().strftime("%H:%M:%S")
        text = self._t.tr("diag.push_ok").format(time=stamp)
        self._prepend_push(text)

    def record_push_failure(self, kind: str, attempt: int) -> None:
        """Append a push failure entry to the recent log."""
        text = self._t.tr("diag.push_fail").format(kind=kind, attempt=attempt)
        self._prepend_push(text)

    def showEvent(self, event: QShowEvent) -> None:
        """Start auto refresh when the panel becomes visible."""
        super().showEvent(event)
        self._timer.start()
        self.refresh_requested.emit()

    def hideEvent(self, event: QHideEvent) -> None:
        """Stop auto refresh when the panel is hidden."""
        self._timer.stop()
        super().hideEvent(event)

    def retranslate(self) -> None:
        """Refresh all labels for the active language."""
        self._music_group.setTitle(self._t.tr("diag.music"))
        self._processes_group.setTitle(self._t.tr("diag.processes"))
        self._display_group.setTitle(self._t.tr("diag.display_list"))
        self._system_group.setTitle(self._t.tr("diag.system"))
        self._push_group.setTitle(self._t.tr("diag.push_log"))
        self._title_caption.setText(self._t.tr("diag.title_label"))
        self._artist_caption.setText(self._t.tr("diag.artist"))
        self._album_caption.setText(self._t.tr("diag.album"))
        self._progress_caption.setText(self._t.tr("diag.progress"))
        self._cpu_caption.setText(self._t.tr("diag.cpu"))
        self._memory_caption.setText(self._t.tr("diag.memory"))
        self._load_caption.setText(self._t.tr("diag.load"))
        self._refresh_button.setText(self._t.tr("button.refresh"))
        self._add_display_button.setText(self._t.tr("diag.add_display"))
        self._remove_display_button.setText(self._t.tr("diag.remove_display"))
        self._refresh_display_list()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(self._build_music_group())
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_processes_group())
        splitter.addWidget(self._build_display_group())
        splitter.addWidget(self._build_system_group())
        splitter.setSizes([280, 220, 200])
        root.addWidget(splitter, 1)
        root.addWidget(self._build_push_group(), 1)
        root.addWidget(self._refresh_button)

    def _build_music_group(self) -> QGroupBox:
        form = QFormLayout()
        form.addRow(self._title_caption, self._title_label)
        form.addRow(self._artist_caption, self._artist_label)
        form.addRow(self._album_caption, self._album_label)
        form.addRow(self._progress_caption, self._progress_label)
        row = QHBoxLayout()
        row.addWidget(self._cover_label)
        row.addLayout(form, 1)
        layout = QVBoxLayout(self._music_group)
        layout.addLayout(row)
        return self._music_group

    def _build_processes_group(self) -> QGroupBox:
        layout = QVBoxLayout(self._processes_group)
        layout.addWidget(self._process_list, 1)
        layout.addWidget(self._add_display_button)
        return self._processes_group

    def _build_display_group(self) -> QGroupBox:
        layout = QVBoxLayout(self._display_group)
        layout.addWidget(self._display_list, 1)
        layout.addWidget(self._remove_display_button)
        return self._display_group

    def _build_system_group(self) -> QGroupBox:
        form = QFormLayout(self._system_group)
        form.addRow(self._cpu_caption, self._cpu_label)
        form.addRow(self._memory_caption, self._memory_label)
        form.addRow(self._load_caption, self._load_label)
        return self._system_group

    def _build_push_group(self) -> QGroupBox:
        layout = QVBoxLayout(self._push_group)
        layout.addWidget(self._push_log)
        return self._push_group

    def _apply_media(self, media: MediaInfo | None, cover_bytes: bytes | None) -> None:
        self._cover_label.setPixmap(self._cover_pixmap(cover_bytes))
        if media is None or media.state is MediaState.IDLE:
            self._title_label.setText(self._t.tr("diag.no_media"))
            self._artist_label.setText("-")
            self._album_label.setText("-")
            self._progress_label.setText("--:-- / --:--")
            return
        self._title_label.setText(media.title or "-")
        self._artist_label.setText(media.artist or "-")
        self._album_label.setText(media.album or "-")
        position = format_ms(media.position_ms)
        duration = format_ms(media.duration_ms)
        self._progress_label.setText(f"{position} / {duration}")

    def _apply_processes(self, processes: list[ProcessInfo]) -> None:
        names = self._diagnose_process_names()
        source = names or [item.name for item in processes]
        self._process_list.clear()
        if not source:
            self._process_list.addItem(self._t.tr("diag.process_empty"))
            return
        for name in source:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._process_list.addItem(item)

    def _diagnose_process_names(self) -> list[str]:
        gate = PrivacyGate()
        if not gate.allow(Capability.PROCESSES):
            return []
        adapter = PsutilProcessAdapter(ProcessFilter(collect_all=True))
        items = adapter.collect(gate) or []
        return sorted(item.name for item in items)

    def _apply_system(self, system: SystemInfo | None) -> None:
        if system is None:
            self._cpu_label.setText("-")
            self._memory_label.setText("-")
            self._load_label.setText("-")
            return
        self._cpu_label.setText(f"{system.cpu_percent:.0f}%")
        self._memory_label.setText(f"{system.memory_percent:.0f}%")
        self._load_label.setText(" ".join(f"{value:.2f}" for value in system.load_avg))

    def _cover_pixmap(self, data: bytes | None) -> QPixmap:
        image = QImage.fromData(data) if data else QImage()
        if image.isNull():
            placeholder = QPixmap(COVER_SIZE, COVER_SIZE)
            placeholder.fill(Qt.GlobalColor.lightGray)
            return placeholder
        return QPixmap.fromImage(image).scaled(
            COVER_SIZE,
            COVER_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _prepend_push(self, text: str) -> None:
        self._push_log.insertItem(0, text)
        while self._push_log.count() > PUSH_LOG_LIMIT:
            self._push_log.takeItem(self._push_log.count() - 1)

    def _refresh_display_list(self) -> None:
        self._display_list.clear()
        for name in self._display_names:
            self._display_list.addItem(name)

    def _add_selected_process(self) -> None:
        item = self._process_list.currentItem()
        if item is None:
            return
        self._add_name(item.data(Qt.ItemDataRole.UserRole) or item.text())

    def _remove_selected_display(self) -> None:
        item = self._display_list.currentItem()
        if item is None:
            return
        name = item.text()
        if name in self._display_names:
            self._display_names.remove(name)
            self._refresh_display_list()
            self.display_list_changed.emit(self.display_list())

    def _add_name(self, name: str) -> None:
        cleaned = str(name).strip()
        if not cleaned or cleaned in self._display_names:
            return
        self._display_names.append(cleaned)
        self._refresh_display_list()
        self.display_list_changed.emit(self.display_list())

    def _show_process_menu(self, pos) -> None:
        item = self._process_list.itemAt(pos)
        if item is None:
            return
        self._process_list.setCurrentItem(item)
        menu = QMenu(self)
        action = QAction(self._t.tr("diag.add_display"), self)
        action.triggered.connect(self._add_selected_process)
        menu.addAction(action)
        menu.exec(self._process_list.mapToGlobal(pos))

    def _show_display_menu(self, pos) -> None:
        item = self._display_list.itemAt(pos)
        if item is None:
            return
        self._display_list.setCurrentItem(item)
        menu = QMenu(self)
        action = QAction(self._t.tr("diag.remove_display"), self)
        action.triggered.connect(self._remove_selected_display)
        menu.addAction(action)
        menu.exec(self._display_list.mapToGlobal(pos))
