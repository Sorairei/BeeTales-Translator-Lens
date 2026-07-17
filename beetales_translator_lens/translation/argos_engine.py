"""Offline Argos Translate engine with explicit route execution."""

from __future__ import annotations

import importlib.util
import logging
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from beetales_translator_lens.translation.argos_support import configure_argos_environment
from beetales_translator_lens.translation.base import TranslationEngine
from beetales_translator_lens.translation.models import TranslationResult
from beetales_translator_lens.translation.text_normalizer import split_message_prefix

LOGGER = logging.getLogger(__name__)


class ArgosTranslationEngine(TranslationEngine):
    def __init__(
        self,
        *,
        translator: Callable[[str, str, str], str] | None = None,
        model_root: Path | None = None,
        preserve_message_prefixes: bool = True,
    ) -> None:
        self._translator = translator
        self._model_root = model_root
        self.preserve_message_prefixes = preserve_message_prefixes

    @staticmethod
    def is_available() -> bool:
        return importlib.util.find_spec("argostranslate") is not None

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        return self.translate_route(text, [source_language, target_language])

    def translate_route(self, text: str, route: list[str]) -> TranslationResult:
        started = perf_counter()
        source = route[0] if route else ""
        target = route[-1] if route else ""
        if not text.strip():
            return self._error(text, source, target, route, started, "There is no text to translate.")
        if len(route) == 1:
            return TranslationResult(text, text, source, target, route, (perf_counter() - started) * 1000)
        if len(route) < 2:
            return self._error(text, source, target, route, started, "The translation route is invalid.")
        try:
            translator = self._translator or self._load_translator()
            output = text
            for route_source, route_target in zip(route, route[1:]):
                output = self._translate_lines(output, route_source, route_target, translator)
            return TranslationResult(
                text,
                output,
                source,
                target,
                list(route),
                (perf_counter() - started) * 1000,
            )
        except Exception as exc:
            LOGGER.exception("Local translation failed for route %s", route)
            return self._error(text, source, target, route, started, f"Translation failed: {exc}")

    def _load_translator(self) -> Callable[[str, str, str], str]:
        if not self.is_available():
            raise RuntimeError("Argos Translate is not installed.")
        configure_argos_environment(self._model_root)
        from argostranslate.translate import translate

        self._translator = translate
        return translate

    def _translate_lines(
        self,
        text: str,
        source: str,
        target: str,
        translator: Callable[[str, str, str], str],
    ) -> str:
        translated_lines: list[str] = []
        for line in text.split("\n"):
            if not line:
                translated_lines.append("")
                continue
            prefix, body = split_message_prefix(line) if self.preserve_message_prefixes else ("", line)
            translated_lines.append(prefix + translator(body, source, target))
        return "\n".join(translated_lines)

    @staticmethod
    def _error(
        text: str,
        source: str,
        target: str,
        route: list[str],
        started: float,
        message: str,
    ) -> TranslationResult:
        return TranslationResult(
            text,
            "",
            source,
            target,
            list(route),
            (perf_counter() - started) * 1000,
            message,
        )
