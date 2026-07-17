"""PaddleOCR adapter tests using small in-memory fake backends."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from beetales_translator_lens.ocr.paddle_engine import PaddleOCREngine


def sample_image() -> np.ndarray:
    return np.zeros((80, 160, 3), dtype=np.uint8)


class V3Backend:
    def predict(self, image: np.ndarray) -> list[dict[str, object]]:
        assert image.flags.c_contiguous
        return [
            {
                "res": {
                    "rec_texts": ["second", "ignored", "first"],
                    "rec_scores": np.array([0.91, 0.2, 0.97]),
                    "rec_polys": np.array(
                        [
                            [[10, 40], [80, 40], [80, 60], [10, 60]],
                            [[5, 70], [40, 70], [40, 78], [5, 78]],
                            [[8, 10], [70, 10], [70, 30], [8, 30]],
                        ]
                    ),
                }
            }
        ]


def test_v3_results_are_filtered_sorted_and_structured(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    def factory(**kwargs: Any) -> V3Backend:
        calls.append(kwargs)
        return V3Backend()

    engine = PaddleOCREngine(backend_factory=factory, model_root=tmp_path)
    result = engine.recognize(sample_image(), "pl")

    assert result.error is None
    assert result.full_text == "first\nsecond"
    assert [line.text for line in result.lines] == ["first", "second"]
    assert result.lines[0].bounding_box[0] == (8, 10)
    assert result.average_confidence == 0.94
    assert calls[0]["lang"] == "pl"
    assert calls[0]["device"] == "cpu"
    assert calls[0]["enable_mkldnn"] is False


def test_japanese_uses_official_paddle_language_code(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    def factory(**kwargs: Any) -> V3Backend:
        calls.append(kwargs)
        return V3Backend()

    PaddleOCREngine(backend_factory=factory, model_root=tmp_path).recognize(sample_image(), "ja")

    assert calls[0]["lang"] == "japan"


def test_backend_is_cached_per_language(tmp_path: Path) -> None:
    calls = 0

    def factory(**kwargs: Any) -> V3Backend:
        nonlocal calls
        calls += 1
        return V3Backend()

    engine = PaddleOCREngine(backend_factory=factory, model_root=tmp_path)
    engine.recognize(sample_image(), "pt")
    engine.recognize(sample_image(), "pt")

    assert calls == 1


class LegacyBackend:
    def ocr(self, image: np.ndarray, cls: bool = False) -> list[object]:
        assert cls is False
        return [
            [
                [[[1, 2], [20, 2], [20, 10], [1, 10]], ("legacy text", 0.88)],
            ]
        ]


def test_legacy_result_shape_remains_supported(tmp_path: Path) -> None:
    engine = PaddleOCREngine(
        backend_factory=lambda **kwargs: LegacyBackend(),
        model_root=tmp_path,
    )

    result = engine.recognize(sample_image(), "en")

    assert result.full_text == "legacy text"
    assert result.lines[0].confidence == 0.88


class BrokenBackend:
    def predict(self, image: np.ndarray) -> object:
        raise RuntimeError("model unavailable")


def test_backend_errors_are_returned_not_raised(tmp_path: Path) -> None:
    engine = PaddleOCREngine(
        backend_factory=lambda **kwargs: BrokenBackend(),
        model_root=tmp_path,
    )

    result = engine.recognize(sample_image(), "es")

    assert result.full_text == ""
    assert result.error == "OCR failed: model unavailable"


def test_empty_image_is_rejected_before_backend_creation(tmp_path: Path) -> None:
    engine = PaddleOCREngine(
        backend_factory=lambda **kwargs: V3Backend(),
        model_root=tmp_path,
    )

    result = engine.recognize(np.array([], dtype=np.uint8), "en")

    assert result.error == "The OCR image is empty."
