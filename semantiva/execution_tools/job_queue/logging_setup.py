import os
import logging
from datetime import datetime
from semantiva.logger.logger import Logger


def _setup_log(role: str, level: str = "INFO") -> Logger:
    pid = os.getpid()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{role}_{pid}_{ts}.log"

    # Create a logger for the specific role
    logger = logging.getLogger(role)
    logger.setLevel(level)

    # Check if the logger already has handlers to avoid duplicate logs
    if not logger.handlers:
        # Create a file handler
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(
            f"%(asctime)s - {role.upper()} - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(file_handler)

    return Logger(logger=logger)
