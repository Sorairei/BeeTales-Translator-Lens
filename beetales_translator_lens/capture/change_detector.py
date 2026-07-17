"""Low-cost change detection before the future OCR stage."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

import cv2
import numpy as np
from numpy.typing import NDArray

SENSITIVITY_THRESHOLDS = {"low": 0.10, "normal": 0.035, "high": 0.012}


@dataclass(frozen=True, slots=True)
class ChangeResult:
    changed: bool
    changed_ratio: float
    forced: bool = False


class ChangeDetector:
    """Compare grayscale thumbnails and force periodic reads."""

    def __init__(
        self,
        sensitivity: str = "normal",
        force_after_seconds: float = 10.0,
        pixel_difference: int = 18,
        thumbnail_size: tuple[int, int] = (160, 90),
    ) -> None:
        self.sensitivity = sensitivity if sensitivity in SENSITIVITY_THRESHOLDS else "normal"
        self.force_after_seconds = max(0.1, force_after_seconds)
        self.pixel_difference = max(1, min(pixel_difference, 255))
        self.thumbnail_size = thumbnail_size
        self._previous: NDArray[np.uint8] | None = None
        self._last_accepted_at: float | None = None

    def compare(
        self,
        image: NDArray[np.uint8],
        *,
        force: bool = False,
        now: float | None = None,
    ) -> ChangeResult:
        current = self._thumbnail(image)
        timestamp = monotonic() if now is None else now
        periodic = (
            self._last_accepted_at is not None
            and timestamp - self._last_accepted_at >= self.force_after_seconds
        )

        if self._previous is None or self._previous.shape != current.shape:
            self._accept(current, timestamp)
            return ChangeResult(True, 1.0, force)

        difference = cv2.absdiff(current, self._previous)
        changed_ratio = float(np.count_nonzero(difference >= self.pixel_difference) / difference.size)
        changed = force or periodic or changed_ratio >= SENSITIVITY_THRESHOLDS[self.sensitivity]
        # Always retain the newest frame so gradual changes can be detected.
        self._previous = current
        if changed:
            self._last_accepted_at = timestamp
        return ChangeResult(changed, changed_ratio, force or periodic)

    def reset(self) -> None:
        self._previous = None
        self._last_accepted_at = None

    def _accept(self, image: NDArray[np.uint8], timestamp: float) -> None:
        self._previous = image
        self._last_accepted_at = timestamp

    def _thumbnail(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim == 3:
            if image.shape[2] == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.ndim == 2:
            gray = image
        else:
            raise ValueError("The image must have two or three dimensions")
        return cv2.resize(gray, self.thumbnail_size, interpolation=cv2.INTER_AREA)
