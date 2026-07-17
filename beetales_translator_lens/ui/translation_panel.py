"""Floating language and translation panel."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from beetales_translator_lens.constants import APP_NAME, SOURCE_LANGUAGES, TARGET_LANGUAGES


class TranslationPanel(QWidget):
    """Associated panel with capture controls and recognized text output."""

    start_requested = Signal()
    pause_requested = Signal()
    copy_requested = Signal()
    lock_requested = Signal()
    close_requested = Signal()
    language_changed = Signal()
    capture_settings_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("translationPanel")
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(480, 330)
        self._drag_offset: QPoint | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(9, 4, 5, 4)
        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        self.status_label = QLabel("● Waiting for text…")
        self.status_label.setObjectName("statusActive")
        close = QPushButton("×")
        close.setObjectName("closeButton")
        close.setToolTip("Close BeeTales Translator Lens")
        close.clicked.connect(self.close_requested)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)
        title_layout.addWidget(close)
        root.addWidget(self.title_bar)

        language_layout = QGridLayout()
        language_layout.addWidget(QLabel("Source language"), 0, 0)
        language_layout.addWidget(QLabel("Target language"), 0, 1)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        for code, label in SOURCE_LANGUAGES:
            self.source_combo.addItem(label, code)
        for code, label in TARGET_LANGUAGES:
            self.target_combo.addItem(label, code)
        self.source_combo.currentIndexChanged.connect(self.language_changed)
        self.target_combo.currentIndexChanged.connect(self.language_changed)
        language_layout.addWidget(self.source_combo, 1, 0)
        language_layout.addWidget(self.target_combo, 1, 1)
        language_layout.addWidget(QLabel("Capture interval"), 2, 0)
        language_layout.addWidget(QLabel("Change sensitivity"), 2, 1)
        self.interval_combo = QComboBox()
        for value, label in (
            (250, "250 ms"),
            (500, "500 ms"),
            (750, "750 ms"),
            (1000, "1000 ms"),
            (1500, "1500 ms"),
            (2000, "2000 ms"),
            (0, "Manual"),
        ):
            self.interval_combo.addItem(label, value)
        self.sensitivity_combo = QComboBox()
        for value, label in (("low", "Low"), ("normal", "Normal"), ("high", "High")):
            self.sensitivity_combo.addItem(label, value)
        self.interval_combo.currentIndexChanged.connect(self.capture_settings_changed)
        self.sensitivity_combo.currentIndexChanged.connect(self.capture_settings_changed)
        language_layout.addWidget(self.interval_combo, 3, 0)
        language_layout.addWidget(self.sensitivity_combo, 3, 1)
        language_layout.addWidget(QLabel("Image preprocessing"), 4, 0, 1, 2)
        self.profile_combo = QComboBox()
        for value, label in (
            ("automatic", "Automatic"),
            ("dark_background", "Light text on dark background"),
            ("light_background", "Dark text on light background"),
            ("small_text", "Small text"),
            ("japanese", "Japanese horizontal text"),
            ("none", "No preprocessing"),
        ):
            self.profile_combo.addItem(label, value)
        self.profile_combo.currentIndexChanged.connect(self.capture_settings_changed)
        language_layout.addWidget(self.profile_combo, 5, 0, 1, 2)
        root.addLayout(language_layout)

        original_label = QLabel("Detected text:")
        original_label.setObjectName("sectionTitle")
        root.addWidget(original_label)
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setPlaceholderText("Recognized text will appear here.")
        self.original_text.setMaximumHeight(75)
        root.addWidget(self.original_text)

        translation_label = QLabel("Translation:")
        translation_label.setObjectName("sectionTitle")
        root.addWidget(translation_label)
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        self.translated_text.setPlaceholderText("The translation will appear here.")
        root.addWidget(self.translated_text, 1)

        controls = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("accentButton")
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.copy_button = QPushButton("Copy")
        self.lock_button = QPushButton("Lock lens")
        self.lock_button.setCheckable(True)
        self.preview_button = QPushButton("Capture preview")
        self.preview_button.setCheckable(True)
        for button in (
            self.start_button,
            self.pause_button,
            self.copy_button,
            self.lock_button,
            self.preview_button,
        ):
            controls.addWidget(button)
        self.start_button.clicked.connect(self.start_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.copy_button.clicked.connect(self.copy_requested)
        self.lock_button.clicked.connect(self.lock_requested)
        root.addLayout(controls)

        self.preview_label = QLabel("The latest capture will appear here.")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet(
            "background: #111612; border: 1px solid #3e4a42; border-radius: 6px; color: #849087;"
        )
        self.preview_label.setVisible(False)
        self.preview_button.toggled.connect(self.preview_label.setVisible)
        root.addWidget(self.preview_label)

        self.metrics_label = QLabel()
        self.metrics_label.setStyleSheet("color: #93a69a; font-size: 9pt;")
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setVisible(False)
        self.preview_button.toggled.connect(self.metrics_label.setVisible)
        root.addWidget(self.metrics_label)

    def select_languages(self, source: str, target: str) -> None:
        source_index = self.source_combo.findData(source)
        target_index = self.target_combo.findData(target)
        self.source_combo.setCurrentIndex(max(0, source_index))
        self.target_combo.setCurrentIndex(max(0, target_index))

    def selected_languages(self) -> tuple[str, str]:
        return str(self.source_combo.currentData()), str(self.target_combo.currentData())

    def select_capture_settings(
        self,
        interval_ms: int,
        sensitivity: str,
        profile: str,
    ) -> None:
        interval_index = self.interval_combo.findData(interval_ms)
        sensitivity_index = self.sensitivity_combo.findData(sensitivity)
        profile_index = self.profile_combo.findData(profile)
        self.interval_combo.setCurrentIndex(max(0, interval_index))
        self.sensitivity_combo.setCurrentIndex(max(0, sensitivity_index))
        self.profile_combo.setCurrentIndex(max(0, profile_index))

    def selected_capture_settings(self) -> tuple[int, str, str]:
        return (
            int(self.interval_combo.currentData()),
            str(self.sensitivity_combo.currentData()),
            str(self.profile_combo.currentData()),
        )

    def set_status(self, text: str, paused: bool = False) -> None:
        self.status_label.setText(f"● {text}")
        self.status_label.setObjectName("statusPaused" if paused else "statusActive")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_simulated_result(self, original: str, translated: str) -> None:
        self.original_text.setPlainText(original)
        self.translated_text.setPlainText(translated)

    def set_detected_text(self, text: str) -> None:
        self.original_text.setPlainText(text)
        self.translated_text.clear()

    def clear_result(self) -> None:
        self.original_text.clear()
        self.translated_text.clear()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
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
