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
Tests for CLI --strict validation flag behavior.
"""

import subprocess
import sys


def test_cli_strict_flag_exits_on_invalid_params(tmp_path):
    """Test that CLI --strict flag exits non-zero when invalid parameters are detected."""

    # Create a YAML with invalid parameters
    bad_yaml = tmp_path / "bad_pipeline.yaml"
    bad_yaml.write_text(
        """
pipeline:
  nodes:
    - processor: FloatMultiplyOperationWithDefault
      parameters:
        factor: 2.0
        facotr: 3.0  # Typo - invalid parameter
        invalid_param: "test"  # Another invalid parameter
"""
    )

    # Run CLI inspect with --strict flag
    result = subprocess.run(
        [sys.executable, "-m", "semantiva.cli", "inspect", str(bad_yaml), "--strict"],
        capture_output=True,
        text=True,
        cwd=tmp_path.parent.parent,  # Run from semantiva root
    )

    # Should exit with non-zero code
    assert result.returncode == 1

    # Should report the invalid parameters
    assert "Invalid configuration parameters:" in result.stdout
    assert "facotr" in result.stdout
    assert "invalid_param" in result.stdout


def test_cli_strict_flag_succeeds_on_valid_params(tmp_path):
    """Test that CLI --strict flag exits zero when all parameters are valid."""

    # Create a YAML with valid parameters
    good_yaml = tmp_path / "good_pipeline.yaml"
    good_yaml.write_text(
        """
pipeline:
  nodes:
    - processor: FloatMultiplyOperationWithDefault
      parameters:
        factor: 2.0  # Valid parameter
"""
    )

    # Run CLI inspect with --strict flag
    result = subprocess.run(
        [sys.executable, "-m", "semantiva.cli", "inspect", str(good_yaml), "--strict"],
        capture_output=True,
        text=True,
        cwd=tmp_path.parent.parent,  # Run from semantiva root
    )

    # Should exit with zero code
    assert result.returncode == 0

    # Should not report any invalid parameters
    assert "Invalid configuration parameters:" not in result.stdout


def test_cli_non_strict_ignores_invalid_params(tmp_path):
    """Test that CLI without --strict flag reports but doesn't exit on invalid parameters."""

    # Create a YAML with invalid parameters
    bad_yaml = tmp_path / "bad_pipeline.yaml"
    bad_yaml.write_text(
        """
pipeline:
  nodes:
    - processor: FloatMultiplyOperationWithDefault
      parameters:
        factor: 2.0
        facotr: 3.0  # Typo - invalid parameter
"""
    )

    # Run CLI inspect without --strict flag
    result = subprocess.run(
        [sys.executable, "-m", "semantiva.cli", "inspect", str(bad_yaml)],
        capture_output=True,
        text=True,
        cwd=tmp_path.parent.parent,  # Run from semantiva root
    )

    # Should exit with zero code (non-strict mode)
    assert result.returncode == 0

    # Should still report the invalid parameters in output
    assert "Invalid configuration parameters:" in result.stdout
    assert "facotr" in result.stdout
