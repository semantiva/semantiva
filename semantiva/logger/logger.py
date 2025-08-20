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

"""Logging utilities for Semantiva.

All `_SemantivaComponent` subclasses accept an optional ``logger`` argument. When
omitted, a new :class:`Logger` from this module is created automatically.
"""

import sys
import logging
from typing import Optional

DEFAULT_FORMATTER = logging.Formatter(
    "%(asctime)s - %(levelname)-8s - %(message)s (%(module)s)"
)


class Logger:
    """
    A flexible Logger class for configuring logging outputs and verbosity levels.

    This class provides methods to set up logging to the console and/or a file,
    and to adjust the verbosity level of the logs. It wraps around Python's
    built-in logging module to offer a simplified interface for common logging tasks.

    Attributes:
        logger (logging.Logger): The underlying logger instance.
        formatter (logging.Formatter): The formatter for log messages.

    Methods:
        set_verbose_level(verbosity_level: str): Sets the verbosity level of the logger.
        set_console_output(enable: bool): Configures the logger to output to the console.
        set_file_output(file_path: str): Configures the logger to output to a specified file.

    Pickling Support:
        The Logger class supports pickling (serialization) and unpickling (deserialization).
        Since Python's logging.Logger instances are not picklable, the Logger class implements
        custom __getstate__ and __setstate__ methods. When pickled, the logger instance is
        excluded from the serialized state. Upon unpickling, the logger is restored using the
        logger name (defaulting to "Semantiva" if not present). This ensures that Logger
        instances can be safely serialized and deserialized, for example when using multiprocessing
        or saving objects to disk.

        - __getstate__ removes the logger from the state before pickling.
        - __setstate__ restores the logger after unpickling using the stored name.
    """

    logger: logging.Logger
    verbosity_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    _initialized = False

    def __init__(
        self,
        level: Optional[str] = None,
        console_output: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = "Semantiva",
        formatter: Optional[logging.Formatter] = None,
    ):
        """
        Initialize the logger with specified configurations.

        This constructor creates or reuses a logging.Logger instance. If no logger is provided,
        it retrieves the default logger with the specified name (defaulting to "Semantiva"). When
        an instance of Logger is created with a specified log level (e.g., level="DEBUG"), the log
        level of the default logger "Semantiva" is updated accordingly. This means that, regardless
        of where in the code this instance is created, the default logger's log level is changed
        to the new value, affecting all components that use the "Semantiva" logger.

        Note on Pickling:
            The logger instance itself is not pickled. When a Logger object is unpickled,
            the logger is restored using the stored name (or "Semantiva" by default).

        :param level: The logging level for the logger (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        :param console_output: Whether to enable console output for log messages.
        :param logger: An existing logging.Logger instance to use instead of creating a new one.
        :param name: The name for the logger instance, defaults to "Semantiva".
        """

        self.formatter = formatter or DEFAULT_FORMATTER
        if logger is None:
            self.logger = logging.getLogger(name)
        else:
            self.logger = logger
        self.name = name

        # If the Logger class has not been initialized yet, set default values.
        # This ensures that the default log level and console output are only set once.
        if not logger and not self._initialized:
            if level is None:
                level = "INFO"  # Default log level is INFO if not specified
            if console_output is None:
                console_output = True  # Enable console output by default

        # Apply the provided or default log level and console output configuration.
        if level is not None:
            self.set_verbose_level(level)
        if console_output is not None:
            self.set_console_output(console_output)

        # Mark the Logger class as initialized.
        type(self)._initialized = True

    def set_verbose_level(self, verbosity_level: str) -> None:
        """
        Set the verbosity level of the Logger.

        Parameters:
        verbosity_level (str): The verbosity level to set. Must be one of the keys in self.verbosity_map.

        If the provided verbosity level is not valid, an error message is logged and the function returns without changing the verbosity level.
        """
        if verbosity_level not in self.verbosity_map:
            self.logger.error(
                "The verbosity level '%s' is incorrect. Valid levels are: %s.",
                verbosity_level,
                list(self.verbosity_map.keys()),
            )
            return
        previous_level = self.logger.level
        self.logger.setLevel(self.verbosity_map[verbosity_level])
        if previous_level != self.logger.level:
            self.logger.info(
                "Logger verbosity level changed from %s to %s.",
                logging.getLevelName(previous_level),
                verbosity_level,
            )

    def set_console_output(self, enable=True) -> None:
        """
        Enable or disable console output.

        Parameters:
        enable (bool): If True, add a sys.stdout handler; if False, remove it.
        """
        # Check if a console handler is already present
        console_handler_exists = any(
            isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout
            for handler in self.logger.handlers
        )

        if enable:
            if not console_handler_exists:
                # Add the console handler only if not already present
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(self.formatter)
                self.logger.addHandler(console_handler)
        else:
            # Remove any existing console handlers associated with sys.stdout
            self.logger.handlers = [
                handler
                for handler in self.logger.handlers
                if not (
                    isinstance(handler, logging.StreamHandler)
                    and handler.stream == sys.stdout
                )
            ]

    def set_file_output(self, file_path: str) -> None:
        """
        Set a file output handler for the Logger.

        Parameters:
        file_path (str): The path to the file where logs should be written.

        This method attempts to create a file handler that writes log messages to the specified file.
        If the file handler cannot be created, an error message is logged.
        """
        try:
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.error("Failed to set file output: %s", e)

    def __getattr__(self, name):
        # Use __dict__ directly to avoid recursion
        logger = self.__dict__.get("logger", None)
        if logger is None:
            # Use __dict__ to get name, fallback to "Semantiva"
            logger_name = self.__dict__.get("name", "Semantiva")
            logger = logging.getLogger(logger_name)
            self.__dict__["logger"] = logger
        return getattr(logger, name)

    def __getstate__(self):
        """
        Prepare the Logger instance for pickling.

        The logger instance is excluded from the pickled state, as logging.Logger objects
        are not picklable. The logger will be restored after unpickling using the logger name.
        """
        state = self.__dict__.copy()
        state["logger"] = None
        return state

    def __setstate__(self, state):
        """
        Restore the Logger instance after unpickling.

        The logger is recreated using the stored name (or "Semantiva" by default).
        """
        self.__dict__.update(state)
        # Use __dict__ to get name, fallback to "Semantiva"
        logger_name = self.__dict__.get("name", "Semantiva")
        self.__dict__["logger"] = logging.getLogger(logger_name)
