"""Persistent translation-cache tests."""

from __future__ import annotations

from pathlib import Path

from beetales_translator_lens.storage.translation_cache_store import TranslationCacheStore
from beetales_translator_lens.translation.models import TranslationResult


def _result() -> TranslationResult:
    return TranslationResult("Hello", "Hola", "en", "es", ["en", "es"], 8.0)


def test_persistent_cache_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    store = TranslationCacheStore(path, cache_version="test-v1")

    store.save([_result()])
    loaded = store.load()

    assert len(loaded) == 1
    assert loaded[0].translated_text == "Hola"
    assert loaded[0].elapsed_ms == 0.0


def test_cache_version_change_invalidates_entries(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    TranslationCacheStore(path, cache_version="old").save([_result()])

    assert TranslationCacheStore(path, cache_version="new").load() == []


def test_persistent_cache_corruption_is_backed_up(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    path.write_text("not-json", encoding="utf-8")

    assert TranslationCacheStore(path, cache_version="test").load() == []
    assert not path.exists()
    assert len(list(tmp_path.glob("cache.corrupt-*.json"))) == 1
