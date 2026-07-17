"""Background local translation task."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from beetales_translator_lens.translation.argos_engine import ArgosTranslationEngine
from beetales_translator_lens.translation.language_detector import LanguageDetector
from beetales_translator_lens.translation.model_manager import ArgosModelManager
from beetales_translator_lens.translation.models import LanguageDetectionResult
from beetales_translator_lens.translation.route_resolver import TranslationRouteResolver
from beetales_translator_lens.translation.text_normalizer import normalize_ocr_text


@dataclass(frozen=True, slots=True)
class TranslationPreparation:
    normalized_text: str
    source_language: str | None
    target_language: str
    route: list[str] | None
    detection: LanguageDetectionResult | None = None
    error: str | None = None


class TranslationPreparationSignals(QObject):
    completed = Signal(object)


class TranslationPreparationTask(QRunnable):
    """Normalize, detect the language, and inspect installed routes off the UI thread."""

    def __init__(
        self,
        text: str,
        selected_source: str,
        target: str,
        detector: LanguageDetector,
        manager: ArgosModelManager,
        resolver: TranslationRouteResolver,
    ) -> None:
        super().__init__()
        self.text = text
        self.selected_source = selected_source
        self.target = target
        self.detector = detector
        self.manager = manager
        self.resolver = resolver
        self.signals = TranslationPreparationSignals()

    @Slot()
    def run(self) -> None:
        normalized = normalize_ocr_text(self.text)
        if not normalized:
            self.signals.completed.emit(
                TranslationPreparation("", None, self.target, None, error="OCR returned no meaningful text.")
            )
            return
        detection: LanguageDetectionResult | None = None
        source = self.selected_source
        if source == "auto":
            detection = self.detector.detect(normalized)
            if not detection.confident:
                self.signals.completed.emit(
                    TranslationPreparation(
                        normalized,
                        None,
                        self.target,
                        None,
                        detection,
                        detection.error or "The language could not be detected with enough confidence.",
                    )
                )
                return
            source = str(detection.language)
        try:
            route = self.resolver.resolve(source, self.target, self.manager.installed_pairs())
            self.signals.completed.emit(
                TranslationPreparation(normalized, source, self.target, route, detection)
            )
        except Exception as exc:
            self.signals.completed.emit(
                TranslationPreparation(normalized, source, self.target, None, detection, f"Translation setup failed: {exc}")
            )


class TranslationTaskSignals(QObject):
    completed = Signal(object)


class TranslationTask(QRunnable):
    def __init__(self, engine: ArgosTranslationEngine, text: str, route: list[str]) -> None:
        super().__init__()
        self.engine = engine
        self.text = text
        self.route = route
        self.signals = TranslationTaskSignals()

    @Slot()
    def run(self) -> None:
        self.signals.completed.emit(self.engine.translate_route(self.text, self.route))
