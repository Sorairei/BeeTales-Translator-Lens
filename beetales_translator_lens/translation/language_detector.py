"""Short-text language detection restricted to supported languages."""

from __future__ import annotations

import importlib.util
from time import perf_counter
from typing import Any

from beetales_translator_lens.translation.models import LanguageDetectionResult

SUPPORTED_LANGUAGE_NAMES = ("ENGLISH", "SPANISH", "POLISH", "PORTUGUESE", "JAPANESE")


class LanguageDetector:
    def __init__(
        self,
        *,
        minimum_confidence: float = 0.55,
        minimum_margin: float = 0.15,
        backend: Any | None = None,
    ) -> None:
        self.minimum_confidence = minimum_confidence
        self.minimum_margin = minimum_margin
        self._backend = backend

    @staticmethod
    def is_available() -> bool:
        return importlib.util.find_spec("lingua") is not None

    def detect(self, text: str) -> LanguageDetectionResult:
        started = perf_counter()
        meaningful_length = sum(character.isalnum() for character in text)
        if meaningful_length < 4:
            return self._result(None, 0.0, 0.0, started, "Text is too short for reliable language detection.")
        try:
            detector = self._backend or self._build_backend()
            values = list(detector.compute_language_confidence_values(text))
            if not values:
                return self._result(None, 0.0, 0.0, started, "Language detection returned no candidates.")
            first = values[0]
            second_value = float(values[1].value) if len(values) > 1 else 0.0
            confidence = float(first.value)
            margin = confidence - second_value
            code = first.language.iso_code_639_1.name.lower()
            if confidence < self.minimum_confidence or margin < self.minimum_margin:
                return self._result(
                    None,
                    confidence,
                    margin,
                    started,
                    "The language could not be detected with enough confidence.",
                )
            return self._result(code, confidence, margin, started)
        except Exception as exc:
            return self._result(None, 0.0, 0.0, started, f"Language detection failed: {exc}")

    def _build_backend(self) -> Any:
        if not self.is_available():
            raise RuntimeError("Lingua is not installed.")
        from lingua import Language, LanguageDetectorBuilder

        languages = [Language.from_str(name) for name in SUPPORTED_LANGUAGE_NAMES]
        self._backend = LanguageDetectorBuilder.from_languages(*languages).build()
        return self._backend

    @staticmethod
    def _result(
        language: str | None,
        confidence: float,
        margin: float,
        started: float,
        error: str | None = None,
    ) -> LanguageDetectionResult:
        return LanguageDetectionResult(
            language,
            confidence,
            margin,
            (perf_counter() - started) * 1000,
            error,
        )
