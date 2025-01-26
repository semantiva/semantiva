import pytest
import logging
import os
from semantiva.logger import Logger


@pytest.fixture(autouse=True)
def clean_logger():
    """Fixture to clean up logger handlers before and after each test."""
    logger = Logger()
    logger.logger.handlers.clear()  # Remove existing handlers before test
    yield logger  # Provide fresh logger instance

    # Cleanup: Remove all handlers after the test to avoid conflicts
    for handler in logger.logger.handlers[:]:
        handler.close()
        logger.logger.removeHandler(handler)


@pytest.fixture
def logger_instance(clean_logger):
    """Fixture to provide a clean Logger instance for tests."""
    return clean_logger


def test_set_verbose_level(logger_instance):
    """Test setting verbosity levels."""
    logger_instance.set_verbose_level("INFO")
    assert logger_instance.logger.level == logging.INFO

    logger_instance.set_verbose_level("ERROR")
    assert logger_instance.logger.level == logging.ERROR


def test_console_output(capsys, logger_instance):
    """Test that console output is working."""
    logger_instance.set_verbose_level("INFO")
    logger_instance.set_console_output()
    logger_instance.info("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.out


def test_delegate_to_logger(logger_instance):
    """Test delegation of methods to the underlying logger."""
    assert hasattr(logger_instance, "info")
    assert hasattr(logger_instance, "error")
    # Test delegation by calling an underlying method
    logger_instance.info("Delegation test message")


def test_file_output(logger_instance):
    """Test that file output is working."""
    file_path = "test_log.log"

    # Set logger to write to file
    logger_instance.set_verbose_level("INFO")
    logger_instance.set_file_output(file_path)

    # Write test log message
    logger_instance.info("File test message")

    # Ensure file handler flushes before closing
    for handler in logger_instance.logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    # Read from log file before closing handlers
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Verify log entry exists
    assert "File test message" in content, "Log message was not written to file"

    # Cleanup: Close and remove file handlers
    for handler in logger_instance.logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger_instance.logger.removeHandler(handler)

    # Remove test log file
    os.remove(file_path)


if __name__ == "__main__":
    pytest.main()
