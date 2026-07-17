"""Background tasks that never modify widgets directly."""

from .capture_worker import CaptureTask, FrameAnalysis

__all__ = ["CaptureTask", "FrameAnalysis"]
