from .memory_tracker import MemoryTracker
from .stop_watch import StopWatch


# Create a PerformanceTracker class to track memory/time usage of a
# payload processor


class PerformanceTracker:
    """A performance tracker class to measure memory, time and CPU usage of a payload processor."""

    _memory_tracker: MemoryTracker
    _stop_watch: StopWatch

    def __init__(self, pooling_interval: float = 0.001):
        """
        Initialize the performance tracker.

        Args:
            pooling_interval (float): The interval in seconds between memory checks.
        """
        self._memory_tracker = MemoryTracker(pooling_interval)
        self._stop_watch = StopWatch()

    def start(self):
        """Start the performance tracker."""
        self._memory_tracker.start()
        self._stop_watch.start()

    def stop(self):
        """Stop the performance tracker."""
        self._memory_tracker.stop()
        self._stop_watch.stop()

    def get_peak_memory(self):
        """Get the peak memory usage."""
        return self._memory_tracker.get_peak_memory()

    def get_timers(self):
        """Get the elapsed wall-clock and CPU times."""
        return {
            "wall_time": self._stop_watch.elapsed_wall_time(),
            "cpu_time": self._stop_watch.elapsed_cpu_time(),
        }

    def __str__(self):
        return f"Memory: {self.get_peak_memory()} bytes; Wall Time: {self.get_timers()['wall_time']:.6f}s; CPU Time: {self.get_timers()['cpu_time']:.6f}s"
