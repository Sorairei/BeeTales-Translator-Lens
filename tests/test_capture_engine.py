"""MSS adapter tests that do not access a real display."""

from __future__ import annotations

import numpy as np

from beetales_translator_lens.capture.capture_engine import CaptureEngine
from beetales_translator_lens.capture.screen_region import ScreenRegion


class FakeMSS:
    monitors = [
        {"left": -1920, "top": 0, "width": 3840, "height": 1080},
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": -1920, "top": 0, "width": 1920, "height": 1080},
    ]

    def __enter__(self) -> "FakeMSS":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def grab(self, monitor: dict[str, int]) -> np.ndarray:
        image = np.zeros((monitor["height"], monitor["width"], 4), dtype=np.uint8)
        image[:, :, 0] = 25
        image[:, :, 3] = 255
        return image


def test_capture_is_clipped_and_alpha_is_removed() -> None:
    engine = CaptureEngine(FakeMSS)

    result = engine.capture(ScreenRegion(-2000, 100, 200, 80))

    assert result.region == ScreenRegion(-1920, 100, 120, 80)
    assert result.image.shape == (80, 120, 3)
    assert result.image.flags.c_contiguous


def test_monitor_list_excludes_virtual_desktop_entry() -> None:
    monitors = CaptureEngine(FakeMSS).monitors()

    assert monitors == [
        ScreenRegion(0, 0, 1920, 1080),
        ScreenRegion(-1920, 0, 1920, 1080),
    ]
