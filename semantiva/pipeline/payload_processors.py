# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from typing import Optional
from abc import abstractmethod
from semantiva.context_processors import ContextType
from semantiva.context_processors.context_observer import _ContextObserver
from semantiva.data_types import NoDataType
from .payload import Payload
from semantiva.logger import Logger


class Stopwatch:
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


class _PayloadProcessor(_ContextObserver):
    """Base class for payload processing operations with integrated data and context management."""

    stop_watch: Stopwatch

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)
        self.stop_watch = Stopwatch()

    @abstractmethod
    def _process(self, payload: Payload) -> Payload: ...

    def process(self, payload: Optional[Payload] = None) -> Payload:
        """Execute a data processor on a payload.

        If no payload is provided, a new :class:`~semantiva.pipeline.payload.Payload`
        containing :class:`~semantiva.data_types.NoDataType` and an empty
        :class:`~semantiva.context_processors.ContextType` is created. Subclasses
        must implement :meth:`_process`, which receives the normalized payload and
        returns the processed payload.

        Args:
            payload: Payload to process. If ``None`` an empty payload is created.

        Returns:
            Payload: The processed payload returned by :meth:`_process`.

        Raises:
            NotImplementedError: If :meth:`_process` is not implemented in a subclass.
        """
        if payload is None:
            payload = Payload(NoDataType(), ContextType())
        elif isinstance(payload.context, dict):
            payload = Payload(payload.data, ContextType(payload.context))
        # Normalize None data to NoDataType if the expected input type is NoDataType.
        # This provides ergonomic semantics where callers can pass `None` in place of an explicit
        # `NoDataType()` instance when invoking sources or operations that declare they consume no data.
        try:
            expected_input_type = getattr(self, "input_data_type", lambda: None)()
        except Exception:  # pragma: no cover - defensive
            expected_input_type = None
        if payload.data is None and expected_input_type is NoDataType:
            payload = Payload(NoDataType(), payload.context)
        self.stop_watch.start()
        result = self._process(payload)
        self.stop_watch.stop()
        return result
