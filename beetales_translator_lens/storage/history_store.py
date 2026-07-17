"""Optional, bounded translation history stored without captured images."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from beetales_translator_lens.storage.paths import ensure_data_directories
from beetales_translator_lens.translation.models import TranslationResult

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    timestamp: str
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    route: list[str]

    @classmethod
    def from_result(cls, result: TranslationResult) -> "HistoryEntry":
        return cls(
            datetime.now(timezone.utc).isoformat(),
            result.source_language,
            result.target_language,
            result.original_text,
            result.translated_text,
            list(result.route),
        )

    @classmethod
    def from_mapping(cls, value: Any) -> "HistoryEntry" | None:
        if not isinstance(value, dict):
            return None
        try:
            route = value["route"]
            if not isinstance(route, list) or not all(isinstance(code, str) for code in route):
                return None
            fields = (
                value["timestamp"],
                value["source_language"],
                value["target_language"],
                value["original_text"],
                value["translated_text"],
            )
            if not all(isinstance(field, str) for field in fields):
                return None
            return cls(*fields, list(route))
        except KeyError:
            return None

    @property
    def content_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_language,
            self.target_language,
            self.original_text,
            self.translated_text,
        )


class HistoryStore:
    """Write a small JSON history atomically and recover from corruption."""

    def __init__(self, path: Path | None = None, maximum_entries: int = 1000) -> None:
        self.path = path or ensure_data_directories()["history"] / "translations.json"
        self.maximum_entries = max(10, maximum_entries)
        self._lock = Lock()

    def load(self) -> list[HistoryEntry]:
        with self._lock:
            return self._load_unlocked()

    def append(self, result: TranslationResult) -> bool:
        if not result.succeeded:
            return False
        entry = HistoryEntry.from_result(result)
        with self._lock:
            entries = self._load_unlocked()
            if entries and entries[-1].content_key == entry.content_key:
                return False
            entries.append(entry)
            self._write_unlocked(entries[-self.maximum_entries :])
        return True

    def clear(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()

    def delete(self, timestamp: str) -> bool:
        with self._lock:
            entries = self._load_unlocked()
            retained = [entry for entry in entries if entry.timestamp != timestamp]
            if len(retained) == len(entries):
                return False
            if retained:
                self._write_unlocked(retained)
            elif self.path.exists():
                self.path.unlink()
            return True

    def _load_unlocked(self) -> list[HistoryEntry]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") != 1:
                raise ValueError("Unsupported history format")
            raw_entries = payload.get("entries")
            if not isinstance(raw_entries, list):
                raise ValueError("History entries must be a list")
            return [entry for value in raw_entries if (entry := HistoryEntry.from_mapping(value))]
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            LOGGER.warning("Translation history is corrupt; backing it up: %s", exc)
            self._backup_corrupt_unlocked()
            return []

    def _write_unlocked(self, entries: list[HistoryEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        payload = {"schema_version": 1, "entries": [asdict(entry) for entry in entries]}
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def _backup_corrupt_unlocked(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
        except OSError as exc:
            LOGGER.error("Could not back up corrupt translation history: %s", exc)
