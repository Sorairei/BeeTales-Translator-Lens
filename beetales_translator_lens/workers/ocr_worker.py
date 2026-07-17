"""Background OCR execution without direct widget access."""

from __future__ import annotations

from numpy.typing import NDArray
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from beetales_translator_lens.ocr.base import OCREngine


class OCRTaskSignals(QObject):
    completed = Signal(object)


class OCRTask(QRunnable):
    def __init__(
        self,
        engine: OCREngine,
        image: NDArray,
        source_language: str | None,
    ) -> None:
        super().__init__()
        self.engine = engine
        self.image = image
        self.source_language = source_language
        self.signals = OCRTaskSignals()

    @Slot()
    def run(self) -> None:
        result = self.engine.recognize(self.image, self.source_language)
        self.signals.completed.emit(result)
