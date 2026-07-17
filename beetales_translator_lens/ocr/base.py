"""Common OCR engine contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from numpy.typing import NDArray

from beetales_translator_lens.ocr.models import OCRResult


class OCREngine(ABC):
    """Interface implemented by local OCR backends."""

    @abstractmethod
    def recognize(
        self,
        image: NDArray,
        source_language: str | None = None,
    ) -> OCRResult:
        """Recognize text in an in-memory image."""
