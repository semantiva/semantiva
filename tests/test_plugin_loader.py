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

import importlib.metadata
from unittest.mock import patch, MagicMock
import logging
from semantiva.logger import Logger
from semantiva.registry import load_extensions, SemantivaExtension, plugin_registry


def test_load_plugins_happy_path():
    """Test that the load_plugins function works as expected"""

    # 1) Define a mock plugin class that subclasses SemantivaPlugin
    class MockExtension(SemantivaExtension):
        """Mock extension for testing"""

        def __init__(self):
            super().__init__()
            self.register_called = False

        def register(self):
            self.register_called = True

    # patch the class constructor to track how many times it's called
    with (
        patch.object(MockExtension, "__init__", return_value=None) as mock_init,
        patch.object(MockExtension, "register") as mock_register,
        patch("importlib.metadata.entry_points") as mock_entry_points,
    ):
        mock_entry_point = MagicMock()
        mock_entry_point.name = "mock_extension"
        mock_entry_point.load.return_value = MockExtension
        mock_entry_points.return_value = [mock_entry_point]

        load_extensions(["mock_extension"])

        # Now we check if the constructor was called, and whether register(...) was called
        mock_init.assert_called_once()
        mock_register.assert_called_once()


def test_load_missing_spec(caplog):
    """Test that a warning is printed if the user requests a extension that doesn't exist."""
    with patch.object(importlib.metadata, "entry_points", return_value=[]):
        plugin_registry.logger = Logger()
        with caplog.at_level(
            logging.WARNING, logger=plugin_registry.logger.logger.name
        ):
            load_extensions(["non_existent_extension"])

    # The loader should warn that 'non_existent_extension' was not found

    # caplog.text is a single string with all captured logs
    assert (
        "Warning: No Semantiva extension named 'non_existent_extension' was found."
        in caplog.text
    )


def test_load_spec_bad_class(caplog):
    """
    Test that a warning is printed if the extension returned by the entry point
    does not subclass SemantivaExtension.
    """

    class MockClassNoSubclass:
        """Does not subclass SemantivaExtension."""

    mock_entry_point = MagicMock()
    mock_entry_point.name = "bad_spec"
    mock_entry_point.load.return_value = MockClassNoSubclass

    with patch.object(
        importlib.metadata, "entry_points", return_value=[mock_entry_point]
    ):
        plugin_registry.logger = Logger()
        with caplog.at_level(
            logging.WARNING, logger=plugin_registry.logger.logger.name
        ):
            load_extensions(["bad_spec"])

    assert (
        "Warning: Entry point 'bad_spec' does not reference a SemantivaExtension subclass. Skipping."
        in caplog.text
    )
