"""OCR text normalization and chat-prefix tests."""

from beetales_translator_lens.translation.text_normalizer import (
    normalize_ocr_text,
    split_message_prefix,
)


def test_normalization_preserves_unicode_case_and_message_lines() -> None:
    source = "  Jan:   Czy ktoś chce zagrać?  \n\n Anna:  Sí, mañana. \n !!! "

    assert normalize_ocr_text(source) == "Jan: Czy ktoś chce zagrać?\nAnna: Sí, mañana."


def test_message_prefix_patterns_are_preserved() -> None:
    assert split_message_prefix("Jan: Hello there") == ("Jan: ", "Hello there")
    assert split_message_prefix("[Player 1] Ready") == ("[Player 1] ", "Ready")
    assert split_message_prefix("<Alice> Bom dia") == ("<Alice> ", "Bom dia")


def test_plain_line_has_no_prefix() -> None:
    assert split_message_prefix("This is a normal sentence.") == ("", "This is a normal sentence.")
