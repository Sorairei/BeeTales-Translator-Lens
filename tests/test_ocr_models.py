"""OCR result model tests."""

from beetales_translator_lens.ocr.models import OCRLine, OCRResult


def test_average_confidence_uses_all_lines() -> None:
    result = OCRResult(
        full_text="one\ntwo",
        lines=[OCRLine("one", 0.8), OCRLine("two", 0.6)],
        elapsed_ms=10,
        language="en",
    )

    assert result.average_confidence == 0.7
    assert result.succeeded is True


def test_empty_error_result_has_zero_confidence() -> None:
    result = OCRResult("", [], 1, error="failed")

    assert result.average_confidence == 0.0
    assert result.succeeded is False
