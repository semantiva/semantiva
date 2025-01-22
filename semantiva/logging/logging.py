import sys
import logging


class Logger:
    """
    Singleton Logger class for flexible logging configurations.
    """

    _instance = None
    logger: logging.Logger

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

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
        """Set Logger verbosity level"""
        if verbosity_level not in self.verbosity_map:
            raise ValueError(
                f"The verbosity level is incorrect. Got {verbosity_level}."
            )
        self.logger.setLevel(self.verbosity_map[verbosity_level])

    def set_console_output(self):
        """Set console output handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def set_file_output(self, file_path: str):
        """Set file output handler"""
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def __getattr__(self, name):
        """
        Delegate attribute access to the underlying logger instance.
        """
        return getattr(self.logger, name)
