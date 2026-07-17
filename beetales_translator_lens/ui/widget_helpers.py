"""Shared sizing helpers for compact, DPI-safe interface controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox


def configure_combo_box(
    combo: QComboBox,
    *,
    minimum_width: int = 150,
    popup_width: int | None = None,
) -> None:
    """Keep the selected text and every drop-down item readable."""

    combo.setMinimumWidth(minimum_width)
    combo.setMinimumContentsLength(12)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMaxVisibleItems(12)
    view = combo.view()
    view.setTextElideMode(Qt.TextElideMode.ElideNone)
    content_width = max(minimum_width, view.sizeHintForColumn(0) + 36)
    view.setMinimumWidth(max(content_width, popup_width or 0))
