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

"""
Provides a helper to configure role-specific loggers for both master and worker
components in Semantiva's job-queue system. Each logger writes to a unique file
under the `logs/` directory (or a custom directory), incorporating process ID
and timestamp in the filename.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from semantiva.logger.logger import Logger


def _setup_log(
    role: str,
    level: str = "INFO",
    console_output: bool = True,
    logs_dir: Optional[str] = None,
) -> Logger:
    """
    Initialize and return a role-specific Logger that writes to a timestamped file.

    Args:
        role:          Identifier for the component (e.g., "master", "worker_1").
        level:         Logging level as a string (e.g., "DEBUG", "INFO").
        console_output: Whether to also send logs to the console.
        logs_dir:      Optional base directory for log files. If None, will default to "./logs".

    Returns:
        A semantiva.logger.Logger wrapping a standard Python logger configured
        to emit messages to "{base}/{role}_{pid}_{timestamp}.log".
    """
    # Determine process ID and current timestamp for unique log filenames
    pid = os.getpid()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Resolve base logs directory
    base_dir = logs_dir or os.path.join(os.getcwd(), "logs")

    # Ensure the directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Construct full filename
    filename = os.path.join(base_dir, f"{role}_{pid}_{ts}.log")
    # Create a formatter for file output
    formatter = logging.Formatter(
        f"%(asctime)s - {role} - %(levelname)s - %(message)s (%(module)s)"
    )

    # Retrieve or create a standard Python logger by name
    logger = logging.getLogger(role)
    logger.setLevel(level)

    # Only add a file handler if none exist yet (avoid duplicates)
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Optionally add a console handler
    if console_output and not any(
        isinstance(h, logging.StreamHandler) for h in logger.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Wrap and return the Semantiva Logger
    return Logger(logger=logger, console_output=console_output, formatter=formatter)
