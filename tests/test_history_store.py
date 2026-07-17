"""Optional translation-history persistence tests."""

from __future__ import annotations

from pathlib import Path

from beetales_translator_lens.storage.history_store import HistoryStore
from beetales_translator_lens.translation.models import TranslationResult


def _result(index: int) -> TranslationResult:
    return TranslationResult(
        f"Original {index}", f"Translation {index}", "en", "es", ["en", "es"], 12.0
    )


def test_history_is_bounded_and_ignores_adjacent_duplicates(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json", maximum_entries=10)

    for index in range(12):
        assert store.append(_result(index)) is True
    assert store.append(_result(11)) is False

    entries = store.load()
    assert len(entries) == 10
    assert entries[0].original_text == "Original 2"
    assert entries[-1].translated_text == "Translation 11"


def test_history_corruption_is_backed_up(tmp_path: Path) -> None:
    path = tmp_path / "translations.json"
    path.write_text("{broken", encoding="utf-8")

    assert HistoryStore(path).load() == []
    assert not path.exists()
    assert len(list(tmp_path.glob("translations.corrupt-*.json"))) == 1


def test_history_can_be_cleared(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json")
    store.append(_result(1))

    store.clear()

    assert store.load() == []
    assert not store.path.exists()
