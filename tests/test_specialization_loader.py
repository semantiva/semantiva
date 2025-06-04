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
import pytest
from semantiva.specializations.specialization_loader import load_specializations
from semantiva.specializations import SemantivaSpecialization


def test_load_plugins_happy_path():
    """Test that the load_plugins function works as expected"""

    # 1) Define a mock plugin class that subclasses SemantivaPlugin
    class MockSpecialization(SemantivaSpecialization):
        """Mock specialization for testing"""

        def __init__(self):
            super().__init__()
            self.register_called = False

        def register(self):
            self.register_called = True

    # patch the class constructor to track how many times it's called
    with (
        patch.object(MockSpecialization, "__init__", return_value=None) as mock_init,
        patch.object(MockSpecialization, "register") as mock_register,
        patch("importlib.metadata.entry_points") as mock_entry_points,
    ):
        mock_entry_point = MagicMock()
        mock_entry_point.name = "mock_specialization"
        mock_entry_point.load.return_value = MockSpecialization
        mock_entry_points.return_value = [mock_entry_point]

        load_specializations(["mock_specialization"])

        # Now we check if the constructor was called, and whether register(...) was called
        mock_init.assert_called_once()
        mock_register.assert_called_once()


def test_load_missing_spec(caplog):
    """Test that a warning is printed if the user requests a specialization that doesn't exist."""
    with patch.object(importlib.metadata, "entry_points", return_value=[]):
        # Capture output
        with caplog.at_level(logging.WARNING):
            load_specializations(["non_existent_specialization"])

    # The loader should warn that 'non_existent_specialization' was not found

    # caplog.text is a single string with all captured logs
    assert (
        "No specialization named 'non_existent_specialization' was found."
        in caplog.text
    )


def test_load_spec_bad_class(caplog):
    """
    Test that a warning is printed if the specialization returned by the entry point
    does not subclass SemantivaSpecialization.
    """

    class MockClassNoSubclass:
        """Does not subclass SemantivaSpecialization."""

    mock_entry_point = MagicMock()
    mock_entry_point.name = "bad_spec"
    mock_entry_point.load.return_value = MockClassNoSubclass

    with patch.object(
        importlib.metadata, "entry_points", return_value=[mock_entry_point]
    ):
        with caplog.at_level(logging.WARNING):
            load_specializations(["bad_spec"])

    assert (
        "Specialization bad_spec does not subclass SemantivaSpecialization"
        in caplog.text
    )
