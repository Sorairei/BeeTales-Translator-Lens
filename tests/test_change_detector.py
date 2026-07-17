"""Low-cost change detection and periodic forced-read tests."""

import numpy as np

from beetales_translator_lens.capture.change_detector import ChangeDetector


def image(value: int = 0) -> np.ndarray:
    return np.full((120, 200, 3), value, dtype=np.uint8)


def test_first_frame_changes_and_identical_frame_does_not() -> None:
    detector = ChangeDetector(force_after_seconds=30)

    assert detector.compare(image(), now=0).changed is True
    result = detector.compare(image(), now=1)

    assert result.changed is False
    assert result.changed_ratio == 0.0


def test_large_visual_change_is_detected() -> None:
    detector = ChangeDetector(sensitivity="normal")
    detector.compare(image(), now=0)

    result = detector.compare(image(255), now=1)

    assert result.changed is True
    assert result.changed_ratio == 1.0


def test_static_frame_is_forced_after_configured_time() -> None:
    detector = ChangeDetector(force_after_seconds=10)
    detector.compare(image(), now=0)

    result = detector.compare(image(), now=10)

    assert result.changed is True
    assert result.forced is True


def test_manual_force_bypasses_threshold() -> None:
    detector = ChangeDetector()
    detector.compare(image(), now=0)

    result = detector.compare(image(), force=True, now=1)

    assert result.changed is True
    assert result.forced is True
