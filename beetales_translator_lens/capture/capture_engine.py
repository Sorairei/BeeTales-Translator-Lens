"""Regional capture through MSS without temporary files."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable

import mss
import numpy as np
from numpy.typing import NDArray

from beetales_translator_lens.capture.screen_region import ScreenRegion
from beetales_translator_lens.exceptions import BeeTalesError


class CaptureError(BeeTalesError):
    """A usable region could not be captured."""


@dataclass(frozen=True, slots=True)
class CaptureResult:
    image: NDArray[np.uint8]
    region: ScreenRegion
    elapsed_ms: float


class CaptureEngine:
    """Small MSS adapter aware of the complete virtual desktop."""

    def __init__(self, backend_factory: Callable[[], Any] = mss.mss) -> None:
        self._backend_factory = backend_factory

    def capture(self, requested: ScreenRegion) -> CaptureResult:
        if not requested.is_valid:
            raise CaptureError("The selected area is too small.")

        started = perf_counter()
        try:
            with self._backend_factory() as backend:
                virtual = ScreenRegion.from_mapping(backend.monitors[0])
                region = requested.intersection(virtual)
                if region is None:
                    raise CaptureError("The selected area is outside the visible displays.")
                shot = backend.grab(region.as_mss_monitor())
                bgra = np.asarray(shot, dtype=np.uint8)
        except CaptureError:
            raise
        except Exception as exc:
            raise CaptureError(f"This display could not be captured: {exc}") from exc

        if bgra.ndim != 3 or bgra.shape[2] < 3:
            raise CaptureError("The captured data does not contain a valid image.")
        # MSS returns BGRA and OpenCV uses BGR, so only the alpha channel is removed.
        image = np.ascontiguousarray(bgra[:, :, :3])
        return CaptureResult(image, region, (perf_counter() - started) * 1000)

    def monitors(self) -> list[ScreenRegion]:
        """Return every physical monitor while preserving negative coordinates."""

        try:
            with self._backend_factory() as backend:
                return [ScreenRegion.from_mapping(item) for item in backend.monitors[1:]]
        except Exception as exc:
            raise CaptureError(f"Displays could not be detected: {exc}") from exc
