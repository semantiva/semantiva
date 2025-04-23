"""
Provides a helper to configure role-specific loggers for both master and worker
components in Semantiva's job-queue system. Each logger writes to a unique file
under the `logs/` directory, incorporating process ID and timestamp in the filename.
"""

import os
import logging
from datetime import datetime
from semantiva.logger.logger import Logger


def _setup_log(role: str, level: str = "INFO", console_output: bool = True) -> Logger:
    """
    Initialize and return a role-specific Logger that writes to a timestamped file.

    Args:
        role:   Identifier for the component (e.g., "master", "worker_1").
        level:  Logging level as a string (e.g., "DEBUG", "INFO").

    Returns:
        A semantiva.logger.Logger wrapping a standard Python logger configured
        to emit messages to `logs/{role}_{pid}_{timestamp}.log`.
    """
    # Determine process ID and current timestamp for unique log filenames
    pid = os.getpid()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{role}_{pid}_{ts}.log"

    # Retrieve or create a standard Python logger by name
    logger = logging.getLogger(role)
    logger.setLevel(level)

    # Only add a handler if one does not already exist (to prevent duplicates)
    if not logger.handlers:
        # Ensure the logs directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Create a file handler that writes to the designated logfile
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)

        # Define a log message format including timestamp, role, level, and message
        formatter = logging.Formatter(
            f"%(asctime)s - {role.upper()} - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Attach the handler to the logger
        logger.addHandler(file_handler)

    # Wrap the Python logger in Semantiva’s Logger abstraction
    return Logger(logger=logger, console_output=True, formatter=formatter)
