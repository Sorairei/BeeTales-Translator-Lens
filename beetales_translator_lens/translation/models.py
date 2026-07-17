"""Translation and language-detection result models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranslationResult:
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    route: list[str]
    elapsed_ms: float
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass(frozen=True, slots=True)
class LanguageDetectionResult:
    language: str | None
    confidence: float
    margin: float
    elapsed_ms: float
    error: str | None = None

    @property
    def confident(self) -> bool:
        return self.language is not None and self.error is None
