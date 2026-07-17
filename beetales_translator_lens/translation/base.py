"""Common translation engine contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from beetales_translator_lens.translation.models import TranslationResult


class TranslationEngine(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate text locally between a directly installed pair."""
