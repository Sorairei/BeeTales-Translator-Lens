"""Optional persistent translation cache with version-based invalidation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from beetales_translator_lens.constants import VERSION
from beetales_translator_lens.storage.paths import ensure_data_directories
from beetales_translator_lens.translation.models import TranslationResult

LOGGER = logging.getLogger(__name__)


class TranslationCacheStore:
    def __init__(self, path: Path | None = None, cache_version: str = VERSION) -> None:
        self.path = path or ensure_data_directories()["cache"] / "translations.json"
        self.cache_version = cache_version
        self._lock = Lock()

    def load(self) -> list[TranslationResult]:
        with self._lock:
            if not self.path.exists():
                return []
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict) or payload.get("cache_version") != self.cache_version:
                    return []
                values = payload.get("entries")
                if not isinstance(values, list):
                    raise ValueError("Cache entries must be a list")
                return [result for value in values if (result := self._result_from_mapping(value))]
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                LOGGER.warning("Persistent translation cache is corrupt; backing it up: %s", exc)
                self._backup_corrupt_unlocked()
                return []

    def save(self, results: list[TranslationResult]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            entries = [
                {
                    "original_text": result.original_text,
                    "translated_text": result.translated_text,
                    "source_language": result.source_language,
                    "target_language": result.target_language,
                    "route": result.route,
                }
                for result in results
                if result.succeeded
            ]
            payload = {"cache_version": self.cache_version, "entries": entries}
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.path)

    def clear(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()

    @staticmethod
    def _result_from_mapping(value: Any) -> TranslationResult | None:
        if not isinstance(value, dict):
            return None
        try:
            route = value["route"]
            fields = (
                value["original_text"],
                value["translated_text"],
                value["source_language"],
                value["target_language"],
            )
            if not all(isinstance(field, str) for field in fields):
                return None
            if not isinstance(route, list) or not all(isinstance(code, str) for code in route):
                return None
            return TranslationResult(*fields, list(route), 0.0)
        except KeyError:
            return None

    def _backup_corrupt_unlocked(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
        except OSError as exc:
            LOGGER.error("Could not back up corrupt translation cache: %s", exc)
