import sys
import logging


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
    set_console_output(): Configures the logger to output to the console.
    set_file_output(file_path: str): Configures the logger to output to a specified file.
    """

    logger: logging.Logger

    def __init__(
        self,
        name: str = "SemantivaLogger",
        verbosity_level: str = "INFO",
        console_output: bool = True,
        file_output: bool = False,
        file_path: str = "output_log.log",
    ):
        self.logger = logging.getLogger(name)
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.verbosity_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        self.set_verbose_level(verbosity_level)
        if console_output:
            self.set_console_output()

        if file_output:
            self.set_file_output(file_path)

    def set_verbose_level(self, verbosity_level: str):
        """
        Set the verbosity level of the Logger.

        Parameters:
        verbosity_level (str): The verbosity level to set. Must be one of the keys in self.verbosity_map.

        If the provided verbosity level is not valid, an error message is logged and the function returns without changing the verbosity level.
        """
        if verbosity_level not in self.verbosity_map:
            self.logger.error(
                f"The verbosity level '{verbosity_level}' is incorrect. Valid levels are: {list(self.verbosity_map.keys())}."
            )
            return
        previous_level = self.logger.level
        self.logger.setLevel(self.verbosity_map[verbosity_level])
        self.logger.info(
            f"Logger verbosity level changed from {logging.getLevelName(previous_level)} to {verbosity_level}."
        )

    def set_console_output(self):
        """Set console output handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

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
            self.logger.error(f"Failed to set file output: {e}")

    def __getattr__(self, name):
        """
        Delegate attribute access to the underlying logger instance.
        """
        return getattr(self.logger, name)
