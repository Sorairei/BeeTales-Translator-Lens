"""Image preprocessing profile tests for the future OCR stage."""

import numpy as np

from beetales_translator_lens.capture.image_preprocessor import ImagePreprocessor


def test_none_profile_returns_independent_same_shape_image() -> None:
    source = np.zeros((40, 80, 3), dtype=np.uint8)

    result = ImagePreprocessor().process(source, "none")

    assert result.image.shape == source.shape
    assert result.image is not source
    assert result.profile_used == "none"


def test_automatic_selects_dark_profile() -> None:
    source = np.full((40, 80, 3), 20, dtype=np.uint8)

    result = ImagePreprocessor().process(source, "automatic")

    assert result.profile_used == "dark_background"
    assert result.image.ndim == 2


def test_small_text_profile_doubles_dimensions() -> None:
    source = np.zeros((40, 80, 3), dtype=np.uint8)

    result = ImagePreprocessor().process(source, "small_text")

    assert result.image.shape == (80, 160)
