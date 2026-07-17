"""Local route execution and username preservation tests."""

from beetales_translator_lens.translation.argos_engine import ArgosTranslationEngine


def test_direct_translation_preserves_chat_prefixes() -> None:
    calls: list[tuple[str, str, str]] = []

    def translator(text: str, source: str, target: str) -> str:
        calls.append((text, source, target))
        return text.upper()

    result = ArgosTranslationEngine(translator=translator).translate_route(
        "Jan: hello\n[Anna] good morning",
        ["en", "es"],
    )

    assert result.translated_text == "Jan: HELLO\n[Anna] GOOD MORNING"
    assert calls == [("hello", "en", "es"), ("good morning", "en", "es")]


def test_pivot_route_executes_each_language_pair() -> None:
    def translator(text: str, source: str, target: str) -> str:
        return f"{text}[{source}-{target}]"

    result = ArgosTranslationEngine(translator=translator).translate_route("text", ["pl", "en", "es"])

    assert result.translated_text == "text[pl-en][en-es]"
    assert result.route == ["pl", "en", "es"]


def test_translation_errors_are_returned() -> None:
    def broken(text: str, source: str, target: str) -> str:
        raise RuntimeError("missing model")

    result = ArgosTranslationEngine(translator=broken).translate("hello", "en", "es")

    assert result.error == "Translation failed: missing model"
