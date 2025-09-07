from __future__ import annotations

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

import tempfile
import os
from pathlib import Path
from semantiva.contracts.expectations import (
    discover_from_registry,
    discover_from_modules,
    discover_from_paths,
    validate_components,
)
from semantiva.registry.class_registry import ClassRegistry


def test_all_components_meet_contracts() -> None:
    classes = discover_from_registry()
    diags = validate_components(classes)
    errors = [d for d in diags if d.severity == "error"]
    assert not errors, "Contract violations:\n" + "\n".join(
        f"{d.code} {d.component} @ {d.location}: {d.message}" for d in errors
    )


def test_validate_components_debug_mode():
    """Test that validate_components debug mode provides detailed information."""
    classes = discover_from_registry()

    # Test with debug mode disabled
    diags_normal = validate_components(classes, debug_mode=False)

    # Test with debug mode enabled
    diags_debug = validate_components(classes, debug_mode=True)

    # Both should return the same diagnostics
    assert len(diags_normal) == len(diags_debug)

    # Debug mode should produce additional logging (we can't easily test log output,
    # but we can ensure it doesn't break functionality)
    for diag_normal, diag_debug in zip(diags_normal, diags_debug):
        assert diag_normal.code == diag_debug.code
        assert diag_normal.component == diag_debug.component
        assert diag_normal.severity == diag_debug.severity


def test_class_registry_imports_modules():
    """Test that ClassRegistry.register_modules actually imports modules."""

    # Verify the module gets registered
    _ = ClassRegistry.get_registered_modules().copy()

    # Register a module that contains components
    ClassRegistry.register_modules(["semantiva.examples.test_utils"])

    # Verify module is now registered
    final_modules = ClassRegistry.get_registered_modules()
    assert "semantiva.examples.test_utils" in final_modules

    # The components should be available from the component registry
    from semantiva.contracts.expectations import discover_from_registry

    components = discover_from_registry()
    component_names = [f"{c.__module__}.{c.__qualname__}" for c in components]

    # Should find test_utils components
    test_utils_components = [name for name in component_names if "test_utils" in name]
    assert len(test_utils_components) > 0


def test_discover_from_modules_with_import_errors():
    """Test that discover_from_modules handles import errors gracefully."""
    # Test with a non-existent module
    classes = discover_from_modules(["nonexistent_module"])
    # Should not crash, should return empty or partial results
    assert isinstance(classes, list)

    # Test with a mix of valid and invalid modules
    classes = discover_from_modules(
        ["semantiva.examples.test_utils", "nonexistent_module"]
    )
    # Should find components from the valid module
    assert len(classes) > 0
    assert any("test_utils" in str(cls) for cls in classes)


def test_discover_from_modules_core_components():
    """Test that discover_from_modules works with core semantiva modules."""
    classes = discover_from_modules(["semantiva.examples.test_utils"])

    # Should find components from test_utils
    assert len(classes) > 0

    # Should include specific known components
    class_names = [f"{cls.__module__}.{cls.__qualname__}" for cls in classes]
    assert any("FloatDataType" in name for name in class_names)
    assert any("FloatOperation" in name for name in class_names)
    assert any("FloatValueDataSource" in name for name in class_names)


def test_discover_from_paths_with_python_file():
    """Test that discover_from_paths works with individual Python files."""
    # Create a temporary Python file with a component
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
from semantiva.data_types import BaseDataType
from typing import Dict, Any

class PathTestDataType(BaseDataType[str]):
    '''A test data type for path discovery testing.'''
    
    def validate(self, data: str) -> bool:
        return isinstance(data, str)
    
    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        return {
            "component_type": "data_type",
            "description": "Path test data type"
        }
"""
        )
        temp_file_path = f.name

    try:
        classes = discover_from_paths([temp_file_path])

        # Should find the component from the file
        assert len(classes) > 0
        class_names = [cls.__qualname__ for cls in classes]
        assert "PathTestDataType" in class_names
    finally:
        os.unlink(temp_file_path)


def test_discover_from_paths_with_import_errors():
    """Test that discover_from_paths handles files with import errors gracefully."""
    # Create a temporary Python file with import errors
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
# This should cause an import error
import nonexistent_module_xyz

class ErrorTestComponent:
    pass
"""
        )
        temp_file_path = f.name

    try:
        # Should not crash, should handle gracefully
        classes = discover_from_paths([temp_file_path])

        # Should return a list (might be empty due to import error)
        assert isinstance(classes, list)
    finally:
        os.unlink(temp_file_path)


def test_discover_from_paths_with_directory():
    """Test that discover_from_paths works with directories."""
    # Test with a known directory that contains components
    test_utils_path = Path(__file__).parent.parent / "semantiva" / "examples"

    if test_utils_path.exists():
        classes = discover_from_paths([str(test_utils_path)])

        # Should find components from the directory
        assert len(classes) > 0

        # Should include components from test_utils.py
        class_names = [f"{cls.__module__}.{cls.__qualname__}" for cls in classes]
        assert any("test_utils" in name for name in class_names)


def test_discover_from_nonexistent_path():
    """Test that discover_from_paths handles non-existent paths gracefully."""
    classes = discover_from_paths(["/nonexistent/path/file.py"])

    # Should not crash, should return empty list
    assert isinstance(classes, list)
    # May be empty or may have other components from registry


def test_validate_components_with_core_components():
    """Test validation of core semantiva components."""
    # Get some known core components
    classes = discover_from_modules(["semantiva.examples.test_utils"])

    # Validate them
    diags = validate_components(classes)

    # Should complete without crashing
    assert isinstance(diags, list)

    # All diagnostics should have required fields
    for diag in diags:
        assert hasattr(diag, "code")
        assert hasattr(diag, "component")
        assert hasattr(diag, "severity")
        assert hasattr(diag, "message")
        assert diag.severity in ["error", "warning"]


def test_validate_components_empty_list():
    """Test that validate_components handles empty component list."""
    diags = validate_components([])

    # Should return empty list of diagnostics
    assert isinstance(diags, list)
    assert len(diags) == 0


def test_registry_module_import_error_handling():
    """Test that ClassRegistry handles module import errors gracefully."""
    # This should not crash even if the module doesn't exist
    try:
        ClassRegistry.register_modules(["nonexistent_module_for_testing"])
        # Should complete without raising an exception
    except Exception as e:
        # If an exception is raised, it should be logged, not crash the test
        assert (
            False
        ), f"ClassRegistry.register_modules should handle import errors gracefully, but raised: {e}"
