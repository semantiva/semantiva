import pytest
import logging
import os
from semantiva.logger import Logger


@pytest.fixture
def logger_instance():
    """Fixture to create a Logger instance for testing."""
    return Logger(
        name="TestLogger",
        verbosity_level="DEBUG",
        console_output=True,
        file_output=True,
        file_path="test_log.log",
    )


def test_logger_initialization(logger_instance):
    """Test the initialization of the Logger."""
    assert logger_instance.logger.name == "TestLogger"
    assert logger_instance.logger.level == logging.DEBUG


def test_set_verbose_level(logger_instance):
    """Test setting verbosity levels."""
    logger_instance.set_verbose_level("INFO")
    assert logger_instance.logger.level == logging.INFO

    logger_instance.set_verbose_level("ERROR")
    assert logger_instance.logger.level == logging.ERROR


def test_console_output(capsys):
    """Test that console output is working."""
    logger = Logger(
        name="ConsoleLogger",
        verbosity_level="INFO",
        console_output=True,
        file_output=False,
    )
    logger.info("Test message")

    captured = capsys.readouterr()
    assert "Test message" in captured.out


def test_file_output():
    """Test that file output is working."""
    file_path = "test_log.log"
    logger = Logger(
        name="FileLogger",
        verbosity_level="INFO",
        console_output=False,
        file_output=True,
        file_path=file_path,
    )
    logger.info("File test message")

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    assert "File test message" in content

    # Clean up test log file
    os.remove(file_path)


def test_delegate_to_logger():
    """Test delegation of methods to the underlying logger."""
    logger = Logger(
        name="DelegateLogger",
        verbosity_level="INFO",
        console_output=True,
        file_output=False,
    )
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")

    # Test delegation by calling an underlying method
    logger.info("Delegation test message")


if __name__ == "__main__":
    pytest.main()
