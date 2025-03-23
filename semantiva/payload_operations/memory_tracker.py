# Description: A memory tracker class to measure peak memory usage.
import threading
import psutil


class MemoryTracker:
    """A memory tracker class to measure peak memory usage.
    When the tracker is started, it will pool the memory usage at regular intervals
    in a separate thread."""

    _peak_memory: int
    _pooling_interval: float
    _running: bool
    _thread: threading.Thread
    _stop_event: threading.Event
    _calls: int

    def __init__(self, pooling_interval: float = 0.001):
        """
        Initialize the memory tracker.

        Args:
            pooling_interval (float): The interval in seconds between memory checks.
        """
        self._pooling_interval = pooling_interval
        self._stop_event = threading.Event()
        self.reset()

    def _measure_memory(self):
        """Measure the current memory usage."""
        return psutil.Process().memory_info().rss

    def _pool_memory(self):
        """Pool the memory usage at regular intervals."""
        while self._running:
            current_memory = self._measure_memory()
            self._peak_memory = max(self._peak_memory, current_memory)
            # Interruptible wait instead of sleep
            self._stop_event.wait(timeout=self._pooling_interval)

    def start(self):
        """Start the memory tracker."""
        if not self._running:
            self._running = True
            # Initial memory measurement
            self._peak_memory = self._measure_memory()
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._pool_memory)
            self._thread.start()
            self._calls += 1

    def stop(self):
        """Stop the memory tracker and perform a final memory check."""
        if self._running:
            # Final immediate memory check before joining
            final_memory = self._measure_memory()
            self._peak_memory = max(self._peak_memory, final_memory)

            self._running = False
            self._stop_event.set()  # Immediately interrupt waiting
            self._thread.join()

    def reset(self):
        """Reset the memory tracker by clearing all values."""
        self._peak_memory = 0
        self._running = False
        self._thread = None
        self._stop_event.clear()
        self._calls = 0

    def set_pooling_interval(self, pooling_interval: float):
        """Set the pooling interval for memory checks."""
        self._pooling_interval = pooling_interval

    def peak_memory(self):
        """Return the peak memory usage."""
        return self._peak_memory

    def peak_memory_mb(self):
        """Return the peak memory usage in megabytes (MiB)."""
        return self._peak_memory / (1024 * 1024)
