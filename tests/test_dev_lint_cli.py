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

"""Tests for the `semantiva dev lint` CLI command."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
import textwrap


def run_cli(args, cwd: Path | None = None):
    """Run the semantiva CLI with the given arguments."""
    cmd = [sys.executable, "-m", "semantiva.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def test_lint_handles_import_errors():
    """Test that `dev lint` gracefully handles modules with import errors."""
    # Create a temporary module with import errors
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            textwrap.dedent(
                """
            # This should cause an import error
            import nonexistent_module_that_does_not_exist
            
            class TestComponent:
                pass
        """
            )
        )
        temp_module_path = f.name

    try:
        # Should not crash, should show warning
        result = run_cli(["dev", "lint", "--paths", temp_module_path])

        assert result.returncode == 0  # Should not crash
        assert "Warning:" in result.stdout or "Failed to import" in result.stdout
    finally:
        os.unlink(temp_module_path)


def test_lint_handles_ipython_decorator_errors():
    """Test that `dev lint` gracefully handles IPython-specific code."""
    # Create a temporary module with IPython decorators
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            textwrap.dedent(
                """
            from IPython.core.magic import register_line_magic
            
            @register_line_magic
            def some_magic(line):
                pass
            
            class TestComponent:
                pass
        """
            )
        )
        temp_module_path = f.name

    try:
        # Should not crash, should handle gracefully
        result = run_cli(["dev", "lint", "--paths", temp_module_path])

        assert result.returncode == 0  # Should not crash
        # Should either succeed or show import warning, but not crash
    finally:
        os.unlink(temp_module_path)


def test_lint_core_components_discovery():
    """Test that `dev lint` discovers core Semantiva components without extensions."""
    result = run_cli(["dev", "lint"])

    assert result.returncode == 0

    # Should find core components (output goes to stdout for dev lint)
    output_lines = result.stdout.split("\n")
    component_count_line = [
        line for line in output_lines if "Testing" in line and "components" in line
    ]
    assert len(component_count_line) > 0

    # Extract component count from log line like "2025-09-06 21:19:34,944 - INFO - Testing 5 components (cli)"
    log_parts = component_count_line[0].split()
    testing_index = log_parts.index("Testing")
    component_count = int(log_parts[testing_index + 1])
    assert component_count >= 5  # Should find at least the basic core components

    # Should include some core components
    assert any("semantiva." in line for line in output_lines)


def test_lint_debug_mode():
    """Test that --debug shows detailed component information."""
    result = run_cli(["dev", "lint", "--debug"])

    assert result.returncode == 0

    # Debug mode should show component types and rules (output goes to stdout)
    stdout_output = result.stdout
    assert "Validating" in stdout_output  # Component type detection
    assert (
        "Checking rules:" in stdout_output or "No specific rules apply" in stdout_output
    )  # Rule application
    assert (
        "✓ All checks passed" in stdout_output
        or "ERROR" in stdout_output
        or "WARN" in stdout_output
    )  # Check results


def test_lint_bad_extension_name():
    """Test that invalid extension names don't crash the command."""
    result = run_cli(["dev", "lint", "--extensions", "nonexistent_extension"])

    assert result.returncode == 0  # Should not crash
    # Warnings might go to stderr or stdout, check both
    output = result.stderr + result.stdout
    assert "Warning:" in output  # Should show warning
    assert (
        "No Semantiva extension named" in output or "Failed to import module" in output
    )


def test_lint_module_discovery():
    """Test that --modules works with core Semantiva modules."""
    result = run_cli(["dev", "lint", "--modules", "semantiva.examples.test_utils"])

    assert result.returncode == 0

    # Should find components from the test_utils module
    stdout_output = result.stdout
    assert "semantiva.examples.test_utils" in stdout_output

    # Should find specific components like FloatDataType, FloatOperation, etc.
    assert (
        "FloatDataType" in stdout_output
        or "FloatOperation" in stdout_output
        or "FloatValueDataSource" in stdout_output
    )


def test_lint_yaml_discovery():
    """Test that --yaml discovers components from pipeline configuration."""
    # Create a temporary pipeline YAML with core semantiva components
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            textwrap.dedent(
                """
            pipeline:
              nodes:
                - processor: semantiva.pipeline.pipeline.Pipeline
                  parameters:
                    name: test_pipeline
        """
            )
        )
        yaml_path = f.name

    try:
        result = run_cli(["dev", "lint", "--yaml", yaml_path])

        assert result.returncode == 0

        # Should find the pipeline components mentioned
        stdout_output = result.stdout
        # Look for component discovery messages
        assert "Testing" in stdout_output and "components" in stdout_output
    finally:
        os.unlink(yaml_path)


def test_lint_path_discovery():
    """Test that --paths discovers components from Python files."""
    # Create a temporary Python file with a component
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            textwrap.dedent(
                """
            from semantiva.data_types import BaseDataType
            from semantiva.core.semantiva_component import _SemantivaComponent
            from typing import Dict, Any
            
            class TestDataType(BaseDataType[str]):
                '''A test data type for testing dev lint path discovery.'''
                
                def validate(self, data: str) -> bool:
                    return isinstance(data, str)
                
                @classmethod
                def _define_metadata(cls) -> Dict[str, Any]:
                    return {
                        "component_type": "data_type",
                        "description": "Test data type"
                    }
        """
            )
        )
        temp_file_path = f.name

    try:
        result = run_cli(["dev", "lint", "--paths", temp_file_path])

        assert result.returncode == 0

        # Should discover the component from the file
        stdout_output = result.stdout
        assert "TestDataType" in stdout_output
    finally:
        os.unlink(temp_file_path)


def test_lint_validation_results():
    """Test that `dev lint` shows validation results properly."""
    result = run_cli(["dev", "lint"])

    assert result.returncode == 0

    stdout_output = result.stdout

    # Should show either all passed or some issues
    assert (
        "All components passed validation ✓" in stdout_output
        or "with issues" in stdout_output
    )

    # Should show component listing
    assert any("semantiva." in line for line in stdout_output.split("\n"))


def test_lint_export_contracts():
    """Test that --export-contracts generates documentation."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        contracts_file = f.name

    try:
        result = run_cli(["dev", "lint", "--export-contracts", contracts_file])

        assert result.returncode == 0
        assert f"Wrote contract catalog to: {contracts_file}" in result.stdout

        # Check that the file was created and has content
        assert os.path.exists(contracts_file)
        with open(contracts_file, "r") as f:
            content = f.read()
            assert len(content) > 0
            # The content should contain validation rules
            assert "SVA" in content or "error" in content or "Code" in content
    finally:
        if os.path.exists(contracts_file):
            os.unlink(contracts_file)


def test_lint_component_type_detection_in_debug():
    """Test that debug mode correctly identifies component types for core components."""
    result = run_cli(
        ["dev", "lint", "--debug", "--modules", "semantiva.examples.test_utils"]
    )

    stdout_output = result.stdout

    # Should detect different component types from test_utils
    assert (
        "Validating DataSource:" in stdout_output
        or "Validating DataIO:" in stdout_output
    )  # FloatValueDataSource, FloatDataSource
    assert "Validating DataOperation:" in stdout_output  # FloatMultiplyOperation, etc.
    assert "Validating DataProbe:" in stdout_output  # FloatBasicProbe
    assert "Validating DataType:" in stdout_output  # FloatDataType
    assert (
        "Validating DataSink:" in stdout_output or "Validating DataIO:" in stdout_output
    )  # FloatDataSink, FloatTxtFileSaver


def test_lint_multiple_discovery_methods():
    """Test using multiple discovery methods together."""
    # Create a simple Python component file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            textwrap.dedent(
                """
            from semantiva.data_types import BaseDataType
            from typing import Dict, Any
            
            class MultiTestDataType(BaseDataType[int]):
                def validate(self, data: int) -> bool:
                    return isinstance(data, int)
                
                @classmethod
                def _define_metadata(cls) -> Dict[str, Any]:
                    return {"component_type": "data_type"}
        """
            )
        )
        temp_file_path = f.name

    try:
        # Use both --modules and --paths
        result = run_cli(
            [
                "dev",
                "lint",
                "--modules",
                "semantiva.examples.test_utils",
                "--paths",
                temp_file_path,
                "--debug",
            ]
        )

        assert result.returncode == 0

        stdout_output = result.stdout

        # Should find components from both discovery methods
        assert "semantiva.examples.test_utils" in stdout_output
        assert "MultiTestDataType" in stdout_output

        # Should show debug information
        assert "Validating" in stdout_output
    finally:
        os.unlink(temp_file_path)


def test_lint_graceful_error_handling():
    """Test that `dev lint` handles various error conditions gracefully."""
    # Test with non-existent path
    result = run_cli(["dev", "lint", "--paths", "/nonexistent/path/file.py"])
    assert result.returncode == 0  # Should not crash

    # Test with empty module list
    result = run_cli(["dev", "lint", "--modules"])
    assert result.returncode == 0  # Should not crash, fall back to default

    # Test with non-existent YAML file - this currently fails rather than being graceful
    result = run_cli(["dev", "lint", "--yaml", "/nonexistent/pipeline.yaml"])
    assert result.returncode != 0  # Currently fails with missing file


def test_lint_no_arguments_uses_registry():
    """Test that `dev lint` with no arguments discovers from registry."""
    result = run_cli(["dev", "lint"])

    assert result.returncode == 0

    # Should find some components from the registry
    stdout_output = result.stdout
    component_count_line = [
        line
        for line in stdout_output.split("\n")
        if "Testing" in line and "components" in line
    ]
    assert len(component_count_line) > 0

    # Extract component count from log line like "2025-09-06 21:19:34,944 - INFO - Testing 5 components (cli)"
    log_parts = component_count_line[0].split()
    testing_index = log_parts.index("Testing")
    component_count = int(log_parts[testing_index + 1])
    assert component_count > 0  # Should find at least some components


def test_lint_error_vs_warning_distinction():
    """Test that `dev lint` properly distinguishes between errors and warnings."""
    result = run_cli(["dev", "lint", "--debug"])

    assert result.returncode == 0

    # The return code should be 0 if only warnings, 1 if errors
    # Since we're testing core components which should be well-formed,
    # we expect return code 0

    stdout_output = result.stdout

    # Should show validation completion
    assert (
        "All components passed validation" in stdout_output
        or "Validation complete:" in stdout_output
    )
