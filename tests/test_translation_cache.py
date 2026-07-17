"""Bounded LRU translation cache tests."""

from beetales_translator_lens.translation.models import TranslationResult
from beetales_translator_lens.translation.translation_cache import TranslationCache


def result(text: str, translated: str = "translated") -> TranslationResult:
    return TranslationResult(text, translated, "en", "es", ["en", "es"], 10)


def test_cache_returns_exact_language_and_text_key() -> None:
    cache = TranslationCache()
    cache.put(result("Hello", "Hola"))

    assert cache.get("en", "es", "Hello").translated_text == "Hola"  # type: ignore[union-attr]
    assert cache.get("en", "pt", "Hello") is None
    assert cache.get("en", "es", "hello") is None


def test_least_recently_used_entry_is_evicted() -> None:
    cache = TranslationCache(maximum_entries=2)
    cache.put(result("one"))
    cache.put(result("two"))
    cache.get("en", "es", "one")
    cache.put(result("three"))

    assert cache.get("en", "es", "one") is not None
    assert cache.get("en", "es", "two") is None
    assert len(cache) == 2


def test_snapshot_can_restore_a_bounded_cache() -> None:
    source = TranslationCache(maximum_entries=3)
    for index in range(3):
        source.put(result(str(index)))

    restored = TranslationCache(maximum_entries=2)
    restored.load(source.snapshot())

    assert len(restored) == 2
    assert restored.get("en", "es", "0") is None
    assert restored.get("en", "es", "2") is not None
