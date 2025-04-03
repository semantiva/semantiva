import pytest
import time
from semantiva.performance_tracker.stop_watch import TimeTracker
from semantiva.performance_tracker.memory_tracker import MemoryTracker
from semantiva.performance_tracker.performance_tracker import PerformanceTracker


@pytest.fixture
def tracker():
    tracker = PerformanceTracker(pooling_interval=0.01)
    yield tracker
    tracker.stop()


def test_initialization(tracker):
    assert tracker._memory_tracker.enabled is True
    assert tracker._stop_watch.enabled is True


def test_trackers_type(tracker):
    assert isinstance(tracker._memory_tracker, MemoryTracker)
    assert isinstance(tracker._stop_watch, TimeTracker)


def test_memory_tracking_enable_disable(tracker):
    tracker.disable_memory_tracking()
    assert tracker._memory_tracker.enabled is False

    tracker.enable_memory_tracking()
    assert tracker._memory_tracker.enabled is True


def test_time_tracking_enable_disable(tracker):
    tracker.disable_time_tracking()
    assert tracker._stop_watch.enabled is False

    tracker.enable_time_tracking()
    assert tracker._stop_watch.enabled is True


def test_start_stop_reset(tracker):
    tracker.start()
    time.sleep(0.05)
    tracker.stop()

    timers = tracker.get_timers()
    peak_memory = tracker.get_peak_memory()

    assert timers["wall_time"] >= 0.05
    assert timers["cpu_time"] >= 0
    assert peak_memory > 0

    tracker.reset()
    timers_after_reset = tracker.get_timers()
    peak_memory_after_reset = tracker.get_peak_memory()

    assert timers_after_reset["wall_time"] == 0
    assert timers_after_reset["cpu_time"] == 0
    assert peak_memory_after_reset == 0


def test_set_memory_pooling_interval(tracker):
    tracker.set_memory_pooling_interval(0.1)
    assert tracker._memory_tracker._pooling_interval == 0.1


def test_str_method(tracker):
    tracker.start()
    time.sleep(0.02)
    tracker.stop()

    output = str(tracker)

    assert "Memory:" in output
    assert "Mb" in output
