"""Panel flotante de idioma y resultado simulado."""

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
    """Panel asociado con controles funcionales y contenido simulado."""

    start_requested = Signal()
    pause_requested = Signal()
    copy_requested = Signal()
    lock_requested = Signal()
    close_requested = Signal()
    language_changed = Signal()

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
        self.status_label = QLabel("● Esperando texto…")
        self.status_label.setObjectName("statusActive")
        close = QPushButton("×")
        close.setObjectName("closeButton")
        close.setToolTip("Cerrar BeeTales Translator Lens")
        close.clicked.connect(self.close_requested)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)
        title_layout.addWidget(close)
        root.addWidget(self.title_bar)

        language_layout = QGridLayout()
        language_layout.addWidget(QLabel("Idioma de origen"), 0, 0)
        language_layout.addWidget(QLabel("Idioma de destino"), 0, 1)
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
        root.addLayout(language_layout)

        original_label = QLabel("Texto detectado:")
        original_label.setObjectName("sectionTitle")
        root.addWidget(original_label)
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setPlaceholderText("El texto reconocido aparecerá aquí.")
        self.original_text.setMaximumHeight(75)
        root.addWidget(self.original_text)

        translation_label = QLabel("Traducción:")
        translation_label.setObjectName("sectionTitle")
        root.addWidget(translation_label)
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        self.translated_text.setPlaceholderText("La traducción aparecerá aquí.")
        root.addWidget(self.translated_text, 1)

        controls = QHBoxLayout()
        self.start_button = QPushButton("Iniciar")
        self.start_button.setObjectName("accentButton")
        self.pause_button = QPushButton("Pausar")
        self.pause_button.setEnabled(False)
        self.copy_button = QPushButton("Copiar")
        self.lock_button = QPushButton("Bloquear lupa")
        self.lock_button.setCheckable(True)
        for button in (self.start_button, self.pause_button, self.copy_button, self.lock_button):
            controls.addWidget(button)
        self.start_button.clicked.connect(self.start_requested)
        self.pause_button.clicked.connect(self.pause_requested)
        self.copy_button.clicked.connect(self.copy_requested)
        self.lock_button.clicked.connect(self.lock_requested)
        root.addLayout(controls)

    def select_languages(self, source: str, target: str) -> None:
        source_index = self.source_combo.findData(source)
        target_index = self.target_combo.findData(target)
        self.source_combo.setCurrentIndex(max(0, source_index))
        self.target_combo.setCurrentIndex(max(0, target_index))

    def selected_languages(self) -> tuple[str, str]:
        return str(self.source_combo.currentData()), str(self.target_combo.currentData())

    def set_status(self, text: str, paused: bool = False) -> None:
        self.status_label.setText(f"● {text}")
        self.status_label.setObjectName("statusPaused" if paused else "statusActive")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_simulated_result(self, original: str, translated: str) -> None:
        self.original_text.setPlainText(original)
        self.translated_text.setPlainText(translated)

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
