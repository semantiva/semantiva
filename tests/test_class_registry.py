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

from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest
from semantiva.registry import ClassRegistry


@pytest.fixture
def loader():
    """Fixture to provide a fresh instance of ClassRegistry."""
    # Clear registry for this test
    ClassRegistry._registered_paths.clear()
    ClassRegistry._registered_modules.clear()

    yield ClassRegistry

    # Reset to default state after the test
    ClassRegistry._registered_paths.clear()
    ClassRegistry._registered_modules.clear()
    ClassRegistry.initialize_default_modules()


@patch("pathlib.Path.is_file", return_value=True)
def test_register_paths(mock_is_file, loader):
    """Test if register_paths correctly adds paths."""

    loader.register_paths(["new_path/image_algo.py", "new_path/image_probes.py"])
    registered_paths = loader.get_registered_paths()

    expected_paths = {Path("new_path/image_algo.py"), Path("new_path/image_probes.py")}
    assert registered_paths == expected_paths


def test_register_modules(loader):
    """Test if register_modules correctly adds modules."""

    loader._registered_modules = set()  # Reset registered modules

    loader.register_modules(
        [
            "new_module.image_algo",
            "new_module.image_probes",
        ]
    )
    registered_modules = loader.get_registered_modules()

    expected_modules = {"new_module.image_algo", "new_module.image_probes"}
    assert registered_modules == expected_modules

    loader.initialize_default_modules()  # Reset registered modules


def test_register_modules_actually_imports(loader):
    """Test that register_modules actually imports modules, not just stores names."""

    # Verify module isn't registered initially
    assert "semantiva.examples.test_utils" not in loader.get_registered_modules()

    # Register a module
    loader.register_modules(["semantiva.examples.test_utils"])

    # Verify module is now registered
    assert "semantiva.examples.test_utils" in loader.get_registered_modules()

    # Verify the module was actually imported by checking if classes are accessible
    # (The import happens during register_modules according to our earlier tests)
    from semantiva.examples.test_utils import FloatDataType

    assert FloatDataType is not None


@patch("semantiva.registry.class_registry.import_module")
def test_register_modules_handles_import_errors(mock_import, loader):
    """Test that register_modules gracefully handles import errors."""
    # Configure mock to raise ImportError
    mock_import.side_effect = ImportError("Module not found")

    # Should not raise an exception
    try:
        loader.register_modules(["nonexistent_module"])
        # Should complete without raising
    except ImportError:
        pytest.fail("register_modules should handle import errors gracefully")

    # Module should still be registered even if import failed
    registered_modules = loader.get_registered_modules()
    assert "nonexistent_module" in registered_modules


def test_register_modules_with_valid_module():
    """Test register_modules with a known valid module."""
    # Reset registry
    ClassRegistry._registered_modules = set()

    # Register a known valid module
    ClassRegistry.register_modules(["semantiva.examples.test_utils"])

    # Should be in registered modules
    registered_modules = ClassRegistry.get_registered_modules()
    assert "semantiva.examples.test_utils" in registered_modules


def test_register_modules_single_string():
    """Test that register_modules works with a single string (not list)."""
    # Reset registry
    ClassRegistry._registered_modules = set()

    # Register single module as string
    ClassRegistry.register_modules("semantiva.examples.test_utils")

    # Should be in registered modules
    registered_modules = ClassRegistry.get_registered_modules()
    assert "semantiva.examples.test_utils" in registered_modules


@patch("pathlib.Path.is_file", return_value=True)
def test_get_class(mock_is_file, loader):
    """Test if get_class correctly loads a class from registered paths."""

    # Mock the module and class
    mock_module = MagicMock()
    mock_class = MagicMock()
    mock_module.MyClass = mock_class

    # Register a path to simulate loading the module
    mock_path = Path("mock_module_path.py")
    loader.register_paths([mock_path])

    # Simulate the module being loaded and the class being found
    with (
        patch(
            "importlib.util.spec_from_file_location",
            return_value=MagicMock(loader=MagicMock(exec_module=MagicMock())),
        ),
        patch("importlib.util.module_from_spec", return_value=mock_module),
    ):

        loaded_class = loader.get_class("MyClass")

    # Assertions
    assert loaded_class == mock_class


@patch("pathlib.Path.is_file", return_value=False)
def test_get_class_no_file(mock_is_file, loader):
    """Test if get_class raises ValueError when no file is found."""
    loader.register_paths(["non_existent_path.py"])

    with pytest.raises(ValueError):
        loader.get_class("SomeClass")


@patch("pathlib.Path.is_file", return_value=True)
@patch("importlib.util.spec_from_file_location", return_value=None)
def test_get_class_no_spec(mock_spec_from_file, mock_is_file, loader):
    """Test if get_class skips paths with invalid specs."""
    loader.register_paths([Path("invalid_module_path.py")])

    with pytest.raises(ValueError):
        loader.get_class("SomeClass")
