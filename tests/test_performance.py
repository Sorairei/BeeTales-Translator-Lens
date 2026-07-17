"""Continuous-pipeline performance counter tests."""

from beetales_translator_lens.performance import PipelinePerformanceMonitor


def test_monitor_tracks_skips_cache_hits_and_bounded_average() -> None:
    monitor = PipelinePerformanceMonitor(sample_size=2)
    monitor.record_request()
    monitor.record_request()
    monitor.record_busy_skip()
    monitor.record_cache_hit()
    monitor.record_completed_cycle(10.0, unchanged=True)
    monitor.record_completed_cycle(20.0)
    monitor.record_completed_cycle(40.0)

    snapshot = monitor.snapshot()

    assert snapshot.capture_requests == 2
    assert snapshot.completed_cycles == 3
    assert snapshot.skipped_busy_ticks == 1
    assert snapshot.unchanged_frames == 1
    assert snapshot.cache_hits == 1
    assert snapshot.average_cycle_ms == 30.0
