"""Non-blocking capture, comparison, and preprocessing task."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from beetales_translator_lens.capture.capture_engine import CaptureEngine, CaptureResult
from beetales_translator_lens.capture.change_detector import ChangeDetector, ChangeResult
from beetales_translator_lens.capture.image_preprocessor import ImagePreprocessor, PreprocessResult
from beetales_translator_lens.capture.screen_region import ScreenRegion


@dataclass(frozen=True, slots=True)
class FrameAnalysis:
    capture: CaptureResult
    change: ChangeResult
    processed_image: NDArray[np.uint8] | None
    preprocessing_ms: float = 0.0
    profile_used: str | None = None


class CaptureTaskSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class CaptureTask(QRunnable):
    """Run one cycle; the controller prevents tasks from accumulating."""

    def __init__(
        self,
        region: ScreenRegion,
        detector: ChangeDetector,
        preprocessor: ImagePreprocessor,
        profile: str,
        *,
        force: bool = False,
        engine: CaptureEngine | None = None,
    ) -> None:
        super().__init__()
        self.region = region
        self.detector = detector
        self.preprocessor = preprocessor
        self.profile = profile
        self.force = force
        self.engine = engine or CaptureEngine()
        self.signals = CaptureTaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            captured = self.engine.capture(self.region)
            change = self.detector.compare(captured.image, force=self.force)
            processed: PreprocessResult | None = None
            if change.changed:
                processed = self.preprocessor.process(captured.image, self.profile)
            analysis = FrameAnalysis(
                capture=captured,
                change=change,
                processed_image=None if processed is None else processed.image,
                preprocessing_ms=0.0 if processed is None else processed.elapsed_ms,
                profile_used=None if processed is None else processed.profile_used,
            )
            self.signals.completed.emit(analysis)
        except Exception as exc:
            self.signals.failed.emit(str(exc))
