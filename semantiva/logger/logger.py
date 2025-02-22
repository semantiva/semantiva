import sys
import logging
from typing import Optional


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
    """

    logger: logging.Logger
    verbosity_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-8s - %(message)s (%(module)s)"
    )

    _initialized = False

    def __init__(
        self,
        level: Optional[str] = None,
        console_output: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = "Semantiva",
    ):
        """
        Initialize the logger with specified configurations.

        This constructor creates or reuses a logging.Logger instance. If no logger is provided,
        it retrieves the default logger with the specified name (defaulting to "Semantiva"). When
        an instance of Logger is created with a specified log level (e.g., level="DEBUG"), the log
        level of the default logger "Semantiva" is updated accordingly. This means that, regardless
        of where in the code this instance is created, the default logger's log level is changed
        to the new value, affecting all components that use the "Semantiva" logger.

        :param level: The logging level for the logger (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        :param console_output: Whether to enable console output for log messages.
        :param logger: An existing logging.Logger instance to use instead of creating a new one.
        :param name: The name for the logger instance, defaults to "Semantiva".
        """
        if logger is None:
            self.logger = logging.getLogger(name)
        else:
            self.logger = logger

        # If the Logger class has not been initialized yet, set default values.
        # This ensures that the default log level and console output are only set once.
        if not self._initialized:
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

    def set_verbose_level(self, verbosity_level: str):
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
        self.logger.info(
            "Logger verbosity level changed from %s to %s.",
            logging.getLevelName(previous_level),
            verbosity_level,
        )

    def set_console_output(self, enable=True):
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

    def set_file_output(self, file_path: str):
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
        """
        Delegate attribute access to the underlying logger instance.
        """
        return getattr(self.logger, name)
