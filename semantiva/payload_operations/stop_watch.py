import time


class StopWatch:
    """
    A stopwatch class to measure wall-clock and CPU execution times.

    The stopwatch can be started, stopped, and reset, and it allows incremental
    time measurement across multiple start-stop operations.
    """

    def __init__(self):
        """
        Initialize the stopwatch by resetting all values.
        """
        self.reset()
        self._start_count = (
            0  # Track the number of times the stopwatch has been started.
        )

    def start(self):
        """
        Start the stopwatch if it is not already running.

        Records the current wall-clock and CPU times as the start times.
        """
        if not self._running:
            self._start_wall_time = time.time()  # Record the current wall-clock time
            self._start_cpu_time = time.process_time()  # Record the current CPU time
            self._running = True  # Mark the stopwatch as running
            self._start_count += 1  # Increment the start count

    def stop(self):
        """
        Stop the stopwatch if it is running and accumulate elapsed times.

        Updates the total elapsed wall-clock and CPU times since the stopwatch was started.
        """
        if self._running:
            self._elapsed_wall_time += (
                time.time() - self._start_wall_time
            )  # Calculate and add wall-clock time
            self._elapsed_cpu_time += (
                time.process_time() - self._start_cpu_time
            )  # Calculate and add CPU time
            self._running = False  # Mark the stopwatch as stopped

    def reset(self):
        """
        Reset all elapsed times and stop the stopwatch.

        Clears the accumulated wall-clock and CPU times and marks the stopwatch as not running.
        """
        self._elapsed_wall_time = 0.0  # Reset accumulated wall-clock time
        self._elapsed_cpu_time = 0.0  # Reset accumulated CPU time
        self._running = False  # Ensure the stopwatch is marked as not running
        self._start_count = 0  # Reset the start count

    def elapsed_wall_time(self):
        """
        Get the total elapsed wall-clock time.

        Returns the accumulated wall-clock time, including the time since the stopwatch
        was last started if it is still running.

        Returns:
            float: Total elapsed wall-clock time in seconds.
        """
        if self._running:
            return self._elapsed_wall_time + (time.time() - self._start_wall_time)
        return self._elapsed_wall_time

    def elapsed_cpu_time(self):
        """
        Get the total elapsed CPU time.

        Returns the accumulated CPU time, including the time since the stopwatch
        was last started if it is still running.

        Returns:
            float: Total elapsed CPU time in seconds.
        """
        if self._running:
            return self._elapsed_cpu_time + (time.process_time() - self._start_cpu_time)
        return self._elapsed_cpu_time

    def __str__(self):
        return f"Calls: {self._start_count}; Elapsed Wall Time: {self.elapsed_wall_time():.6f}s; Elapsed CPU Time: {self.elapsed_cpu_time():.6f}s"


# Example usage:
if __name__ == "__main__":
    stopwatch = StopWatch()

    # Start the stopwatch
    stopwatch.start()
    time.sleep(1)  # Simulate some task by sleeping for 1 second
    stopwatch.stop()  # Stop the stopwatch

    # Print the stopwatch's state
    print(stopwatch)

    # Start the stopwatch again for a second task
    stopwatch.start()
    time.sleep(2)  # Simulate another task by sleeping for 2 seconds
    stopwatch.stop()  # Stop the stopwatch

    # Print the stopwatch's state again
    print(stopwatch)

    # Reset the stopwatch
    stopwatch.reset()
    print(stopwatch)
