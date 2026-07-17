"""Lightweight continuous-pipeline performance counters."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    capture_requests: int
    completed_cycles: int
    skipped_busy_ticks: int
    unchanged_frames: int
    cache_hits: int
    average_cycle_ms: float


class PipelinePerformanceMonitor:
    """Track bounded timing samples without retaining captured content."""

    def __init__(self, sample_size: int = 30) -> None:
        self.capture_requests = 0
        self.completed_cycles = 0
        self.skipped_busy_ticks = 0
        self.unchanged_frames = 0
        self.cache_hits = 0
        self._cycle_samples: deque[float] = deque(maxlen=max(1, sample_size))

    def record_request(self) -> None:
        self.capture_requests += 1

    def record_busy_skip(self) -> None:
        self.skipped_busy_ticks += 1

    def record_completed_cycle(self, elapsed_ms: float, *, unchanged: bool = False) -> None:
        self.completed_cycles += 1
        self._cycle_samples.append(max(0.0, elapsed_ms))
        if unchanged:
            self.unchanged_frames += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def snapshot(self) -> PerformanceSnapshot:
        average = sum(self._cycle_samples) / len(self._cycle_samples) if self._cycle_samples else 0.0
        return PerformanceSnapshot(
            self.capture_requests,
            self.completed_cycles,
            self.skipped_busy_ticks,
            self.unchanged_frames,
            self.cache_hits,
            average,
        )
