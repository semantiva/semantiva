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

from abc import abstractmethod
from typing import Any, Optional
from semantiva.context_processors import ContextType, ContextObserver
from semantiva.data_types import BaseDataType, NoDataType
from .payload import Payload
from semantiva.utils.stopwatch import Stopwatch
from semantiva.logger import Logger


class PayloadProcessor(ContextObserver):
    """Base class for payload processing operations with integrated data and context management."""

    logger: Logger
    stop_watch: Stopwatch

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__()
        self.stop_watch = Stopwatch()
        if logger:
            # If a logger instance is provided, use it
            self.logger = logger
        else:
            # If no logger is provided, create a new Logger instance
            self.logger = Logger()

    @abstractmethod
    def _process(self, payload: Payload) -> Payload: ...

    def process(self, payload: Payload | None = None) -> Payload:
        """
        Public method to execute the payload processing logic.

        This method serves as an entry point to invoke the concrete implementation
        of the `_process` method, which must be defined in subclasses.

        Args:
            *args: Variable-length positional arguments to be passed to the `_process` method.
            **kwargs: Variable-length keyword arguments to be passed to the `_process` method.

        Returns:
            Any: The result of the `_process` method, as determined by the subclass implementation.

        Raises:
            NotImplementedError: If the `_process` method is not implemented in a subclass.
        """
        if payload is None:
            payload = Payload(NoDataType(), ContextType())
        elif isinstance(payload.context, dict):
            payload = Payload(payload.data, ContextType(payload.context))
        self.stop_watch.start()
        result = self._process(payload)
        self.stop_watch.stop()
        return result
