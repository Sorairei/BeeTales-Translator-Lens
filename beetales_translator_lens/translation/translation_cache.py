"""Bounded in-memory least-recently-used translation cache."""

from __future__ import annotations

from collections import OrderedDict

from beetales_translator_lens.translation.models import TranslationResult


class TranslationCache:
    def __init__(self, maximum_entries: int = 500) -> None:
        self.maximum_entries = max(1, maximum_entries)
        self._values: OrderedDict[tuple[str, str, str], TranslationResult] = OrderedDict()

    def get(self, source: str, target: str, normalized_text: str) -> TranslationResult | None:
        key = (source, target, normalized_text)
        value = self._values.get(key)
        if value is not None:
            self._values.move_to_end(key)
        return value

    def put(self, result: TranslationResult) -> None:
        key = (result.source_language, result.target_language, result.original_text)
        self._values[key] = result
        self._values.move_to_end(key)
        while len(self._values) > self.maximum_entries:
            self._values.popitem(last=False)

    def clear(self) -> None:
        self._values.clear()

    def __len__(self) -> int:
        return len(self._values)
