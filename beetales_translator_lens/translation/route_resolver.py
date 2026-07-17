"""Resolve direct or English-pivot translation routes."""

from __future__ import annotations

from collections.abc import Collection


class TranslationRouteResolver:
    def __init__(self, pivot_language: str = "en") -> None:
        self.pivot_language = pivot_language

    def resolve(
        self,
        source_language: str,
        target_language: str,
        installed_pairs: Collection[tuple[str, str]],
    ) -> list[str] | None:
        if source_language == target_language:
            return [source_language]
        pairs = set(installed_pairs)
        if (source_language, target_language) in pairs:
            return [source_language, target_language]
        pivot = self.pivot_language
        if (
            source_language != pivot
            and target_language != pivot
            and (source_language, pivot) in pairs
            and (pivot, target_language) in pairs
        ):
            return [source_language, pivot, target_language]
        return None

    def resolve_available(
        self,
        source_language: str,
        target_language: str,
        available_pairs: Collection[tuple[str, str]],
    ) -> list[str] | None:
        """Use the same preference order for packages available remotely."""

        return self.resolve(source_language, target_language, available_pairs)
