from .memory_tracker import MemoryTracker
from .stop_watch import TimeTracker
from .base_tracker import BaseTracker


class PerformanceTracker(BaseTracker):
    """A performance tracker is a composite class of memory and time trackers.
    It tracks the peak memory usage and elapsed wall-clock and CPU times."""

    _memory_tracker: MemoryTracker
    _stop_watch: TimeTracker
    _pooling_interval: float

    def __init__(
        self,
        pooling_interval: float = 0.001,
        track_time: bool = True,
        track_memory: bool = True,
    ) -> None:
        """
        Initialize the performance tracker.

        Args:
            pooling_interval (float): The interval in seconds between memory checks.
        """
        super().__init__()
        self._pooling_interval = pooling_interval
        self._memory_tracker = MemoryTracker(pooling_interval)
        self._memory_tracker.enabled = track_memory
        self._stop_watch = TimeTracker()
        self._stop_watch.enabled = track_time

    def start(self) -> None:
        """Start the performance tracker."""
        if self._memory_tracker.enabled:
            self._memory_tracker.start()
        if self._stop_watch.enabled:
            self._stop_watch.start()

    def stop(self) -> None:
        """Stop the performance tracker."""
        if self._memory_tracker.enabled:
            self._memory_tracker.stop()
        if self._stop_watch.enabled:
            self._stop_watch.stop()

    def reset(self) -> None:
        """Reset the performance tracker."""
        if self._memory_tracker.enabled:
            self._memory_tracker.reset()
        if self._stop_watch.enabled:
            self._stop_watch.reset()

    def get_peak_memory(self) -> float:
        """Get the peak memory usage."""
        return self._memory_tracker.get_peak_memory

    def get_timers(self) -> dict[str, float]:
        """Get the elapsed wall-clock and CPU times."""
        return {
            "wall_time": self._stop_watch.elapsed_wall_time,
            "cpu_time": self._stop_watch.elapsed_cpu_time,
        }

    def set_memory_pooling_interval(self, pooling_interval: float) -> None:
        """Set the interval in seconds between memory checks."""
        self._memory_tracker.set_pooling_interval(pooling_interval)

    def enable_memory_tracking(self) -> None:
        """Enable memory tracking."""
        self._memory_tracker.enabled = True

    def disable_memory_tracking(self) -> None:
        """Disable memory tracking."""
        self._memory_tracker.enabled = False

    def enable_time_tracking(self) -> None:
        """Enable time tracking."""
        self._stop_watch.enabled = True

    def disable_time_tracking(self):
        """Disable time tracking."""
        self._stop_watch.enabled = False

    def __str__(self) -> str:
        """Provide a summary of current tracking data."""
        summary_parts = []

        if self._stop_watch.enabled:
            summary_parts.append(str(self._stop_watch))

        if self._memory_tracker.enabled:
            summary_parts.append(str(self._memory_tracker))

        return "; ".join(summary_parts)
