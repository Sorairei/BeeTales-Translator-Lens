"""OCR engines and structured recognition results."""

from .base import OCREngine
from .models import OCRLine, OCRResult
from .paddle_engine import PaddleOCREngine

__all__ = ["OCREngine", "OCRLine", "OCRResult", "PaddleOCREngine"]
