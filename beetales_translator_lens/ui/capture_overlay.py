"""Transparent lens that defines the capture area."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QLabel, QSizeGrip, QWidget

from beetales_translator_lens.constants import APP_NAME, LensState
from beetales_translator_lens.capture.screen_region import ScreenRegion
from beetales_translator_lens.platform.windows_dpi import physical_window_rect


class CaptureOverlay(QWidget):
    """Floating window that outlines the inner capture region."""

    geometry_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(260, 130)
        self._locked = False
        self._click_through = False
        self._drag_offset: QPoint | None = None
        self._state = LensState.IDLE

        self.drag_bar = QLabel(f"  {APP_NAME}   • {self._state.value}", self)
        self.drag_bar.setStyleSheet(
            "background: rgba(32,38,34,225); color: #dce9df; padding: 5px 8px;"
            "border: 1px solid #78ad87; border-radius: 6px; font-weight: 600;"
        )
        self.drag_bar.setToolTip("Drag to move the lens")
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("background: rgba(92,137,104,190); width: 16px; height: 16px;")

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        self.size_grip.setVisible(not locked)
        self.set_state(LensState.LOCKED if locked else LensState.IDLE)

    def is_locked(self) -> bool:
        return self._locked

    def set_click_through(self, enabled: bool) -> None:
        self._click_through = enabled
        self.setWindowFlag(Qt.WindowTransparentForInput, enabled)
        self.drag_bar.setVisible(not enabled)
        self.size_grip.setVisible(not enabled and not self._locked)
        if self.isVisible():
            self.show()

    def is_click_through(self) -> bool:
        return self._click_through

    def capture_region(self) -> ScreenRegion:
        """Return only the interior, excluding borders and controls."""

        physical = physical_window_rect(int(self.winId()))
        ratio = float(self.devicePixelRatioF())
        if physical is None:
            global_top_left = self.mapToGlobal(QPoint(0, 0))
            left = round(global_top_left.x() * ratio)
            top = round(global_top_left.y() * ratio)
            width = round(self.width() * ratio)
            height = round(self.height() * ratio)
        else:
            left, top, width, height = physical

        border = max(3, round(4 * ratio))
        top_controls = max(border, round(48 * ratio))
        bottom_margin = max(border, round(7 * ratio))
        return ScreenRegion(
            left + border,
            top + top_controls,
            max(0, width - border * 2),
            max(0, height - top_controls - bottom_margin),
        )

    def set_state(self, state: LensState) -> None:
        self._state = state
        self.drag_bar.setText(f"  {APP_NAME}   • {state.value}")
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor("#e3b45e") if self._state == LensState.PAUSED else QColor("#72bd87")
        painter.setPen(QPen(color, 3))
        painter.setBrush(QColor(15, 22, 17, 12))
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self.drag_bar.setGeometry(10, 8, min(360, self.width() - 36), 34)
        self.size_grip.move(self.width() - self.size_grip.width() - 5, self.height() - self.size_grip.height() - 5)
        self.geometry_changed.emit()

    def moveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().moveEvent(event)
        self.geometry_changed.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._locked and event.button() == Qt.LeftButton and event.position().y() <= 48:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)
