"""Structured OCR results independent from PaddleOCR."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OCRLine:
    text: str
    confidence: float
    bounding_box: list[tuple[int, int]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OCRResult:
    full_text: str
    lines: list[OCRLine]
    elapsed_ms: float
    language: str | None = None
    error: str | None = None

    @property
    def average_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)

    @property
    def succeeded(self) -> bool:
        return self.error is None
