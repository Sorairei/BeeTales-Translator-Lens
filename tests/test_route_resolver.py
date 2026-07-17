"""Direct and English-pivot route resolution tests."""

from beetales_translator_lens.translation.route_resolver import TranslationRouteResolver


def test_direct_route_has_priority() -> None:
    pairs = {("pl", "es"), ("pl", "en"), ("en", "es")}

    assert TranslationRouteResolver().resolve("pl", "es", pairs) == ["pl", "es"]


def test_english_pivot_is_used_when_direct_route_is_missing() -> None:
    pairs = {("pl", "en"), ("en", "es")}

    assert TranslationRouteResolver().resolve("pl", "es", pairs) == ["pl", "en", "es"]


def test_unavailable_and_identity_routes() -> None:
    resolver = TranslationRouteResolver()

    assert resolver.resolve("ja", "pt", set()) is None
    assert resolver.resolve("en", "en", set()) == ["en"]
