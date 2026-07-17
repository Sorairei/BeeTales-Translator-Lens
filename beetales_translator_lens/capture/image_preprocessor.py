"""Initial image preparation profiles for the future OCR stage."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import cv2
import numpy as np
from numpy.typing import NDArray

PROFILES = {
    "automatic",
    "dark_background",
    "light_background",
    "small_text",
    "japanese",
    "none",
}


@dataclass(frozen=True, slots=True)
class PreprocessResult:
    image: NDArray[np.uint8]
    profile_used: str
    elapsed_ms: float


class ImagePreprocessor:
    """Apply moderate transformations without writing captures to disk."""

    def process(self, image: NDArray[np.uint8], profile: str = "automatic") -> PreprocessResult:
        started = perf_counter()
        selected = profile if profile in PROFILES else "automatic"
        if selected == "automatic":
            gray = self._gray(image)
            selected = "dark_background" if float(gray.mean()) < 120 else "light_background"

        if selected == "none":
            output = np.ascontiguousarray(image.copy())
        elif selected == "dark_background":
            gray = self._gray(image)
            output = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
            if float(output.mean()) < 110:
                output = cv2.bitwise_not(output)
        elif selected == "light_background":
            gray = self._gray(image)
            output = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8)).apply(gray)
        elif selected == "small_text":
            output = cv2.resize(self._gray(image), None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            output = cv2.GaussianBlur(output, (0, 0), 1.0)
            output = cv2.addWeighted(
                cv2.resize(self._gray(image), None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC),
                1.6,
                output,
                -0.6,
                0,
            )
        elif selected == "japanese":
            output = cv2.resize(self._gray(image), None, fx=1.75, fy=1.75, interpolation=cv2.INTER_CUBIC)
            output = cv2.bilateralFilter(output, 5, 35, 35)
        else:
            raise AssertionError(f"Unhandled profile: {selected}")

        return PreprocessResult(
            np.ascontiguousarray(output),
            selected,
            (perf_counter() - started) * 1000,
        )

    @staticmethod
    def _gray(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim == 2:
            return image.copy()
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        raise ValueError("The image format is not supported")
