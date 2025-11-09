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

"""CLI inspection output tests for identity payload.

These tests ensure that the inspect command produces output conforming
to the documented CLI contract for both concise and extended modes.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_cli import run_cli


def test_cli_concise_output() -> None:
    """Test that concise mode shows required identity information."""
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    result = run_cli(["inspect", str(yaml_path)])
    assert result.returncode == 0
    out = result.stdout

    # Required fields in concise mode
    assert "Configuration Identity" in out
    assert "Semantic ID: plsemid-" in out
    assert "Config ID:   plcid-" in out
    assert "Run-Space Config ID:" in out
    assert "Required Context Keys:" in out

    # Runtime IDs must not appear
    assert "run-" not in out
    assert "plid-" not in out


def test_cli_concise_excludes_runtime_ids() -> None:
    """Test that concise mode never shows runtime IDs."""
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    result = run_cli(["inspect", str(yaml_path)])
    assert result.returncode == 0
    out = result.stdout

    # Forbidden runtime ID patterns
    forbidden = [
        "plid-",
        "run_space_launch_id",
        "run_space_attempt",
        "run_space_inputs_id",
    ]
    for forbidden_id in forbidden:
        assert forbidden_id not in out, f"Found forbidden ID pattern: {forbidden_id}"


def test_cli_extended_node_lines() -> None:
    """Test that extended mode includes per-node information."""
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    result = run_cli(["inspect", "--extended", str(yaml_path)])
    assert result.returncode == 0
    out = result.stdout

    # Should still have identity section
    assert "Configuration Identity" in out
    assert "Semantic ID: plsemid-" in out

    # Should add nodes section with required fields
    assert "Nodes:" in out or "UUID:" in out
    assert "Node Semantic ID" in out


def test_cli_extended_sweep_summary() -> None:
    """Test that extended mode shows sweep summary fields for sweep-enabled nodes."""
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    result = run_cli(["inspect", "--extended", str(yaml_path)])
    assert result.returncode == 0
    out = result.stdout

    # Sweep summary fields must be present in extended format
    assert "parameters:" in out
    assert "variables:" in out
    assert "mode:" in out
    assert "broadcast:" in out
    assert "collection:" in out


def test_cli_extended_excludes_runtime_ids() -> None:
    """Test that extended mode also excludes runtime IDs."""
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    result = run_cli(["inspect", "--extended", str(yaml_path)])
    assert result.returncode == 0
    out = result.stdout

    # Runtime IDs must not appear
    forbidden = [
        "plid-",
        "run_space_launch_id",
        "run_space_attempt",
        "run_space_inputs_id",
    ]
    for forbidden_id in forbidden:
        assert forbidden_id not in out, f"Found forbidden ID pattern: {forbidden_id}"
