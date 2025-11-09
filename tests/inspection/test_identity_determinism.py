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

"""Tests for identity determinism in pipeline inspection.

These tests ensure that inspection payloads are deterministic and sanitized,
serving as regression prevention for the identity system.
"""

import json
from pathlib import Path

import pytest

from semantiva.inspection.builder import build


@pytest.fixture
def simple_pipeline_config():
    """Simple pipeline configuration for testing."""
    return {
        "pipeline": {
            "nodes": [
                {
                    "name": "source",
                    "processor": "semantiva.examples.test_utils.IntGenerator",
                    "parameters": {"value": 42},
                },
                {
                    "name": "op",
                    "processor": "semantiva.examples.test_utils.IntAdder",
                    "parameters": {"increment": 10},
                },
            ]
        }
    }


@pytest.fixture
def pipeline_with_context_keys():
    """Pipeline that requires context keys."""
    return {
        "pipeline": {
            "nodes": [
                {
                    "name": "source",
                    "processor": "semantiva.examples.test_utils.IntGenerator",
                    "parameters": {},
                },
                {
                    "name": "op",
                    "processor": "semantiva.examples.test_utils.IntAdder",
                    "parameters": {},
                },
            ]
        }
    }


def test_required_context_keys_deterministic(pipeline_with_context_keys):
    """Test that required_context_keys are sorted and deterministic."""
    payload1 = build(pipeline_with_context_keys)
    payload2 = build(pipeline_with_context_keys)

    keys1 = payload1.get("required_context_keys", [])
    keys2 = payload2.get("required_context_keys", [])

    # Keys should be sorted
    assert keys1 == sorted(keys1), "Required context keys must be sorted"
    # Multiple runs should produce identical results
    assert keys1 == keys2, "Required context keys must be deterministic"


def test_forbidden_runtime_fields_absent(simple_pipeline_config):
    """Test that inspection payload excludes all runtime/preview fields."""
    payload = build(simple_pipeline_config)
    payload_json = json.dumps(payload)

    # List of forbidden field patterns that should never appear in inspection
    forbidden = [
        "plid-",  # pipeline_id prefix
        "run-",  # run_id prefix
        "run_space_launch_id",
        "run_space_attempt",
        "run_space_index",
        "run_space_context",
        "run_space_inputs_id",  # Only spec_id allowed, not inputs_id
        "preprocessor_view",  # UI-only field
    ]

    for forbidden_field in forbidden:
        assert (
            forbidden_field not in payload_json
        ), f"Forbidden field '{forbidden_field}' found in inspection payload"


def test_identity_structure(simple_pipeline_config):
    """Test that identity structure conforms to specification."""
    payload = build(simple_pipeline_config)
    identity = payload.get("identity")

    assert identity is not None, "Identity must be present"
    assert "semantic_id" in identity, "semantic_id is required"
    assert "config_id" in identity, "config_id is required"

    # Verify ID prefixes
    assert identity["semantic_id"].startswith(
        "plsemid-"
    ), "semantic_id must have plsemid- prefix"
    assert identity["config_id"].startswith(
        "plcid-"
    ), "config_id must have plcid- prefix"

    # run_space can be None or dict, but if dict, should only have spec_id
    run_space = identity.get("run_space")
    if run_space is not None:
        assert isinstance(run_space, dict), "run_space must be dict or None"
        # inputs_id should not be present
        assert (
            "inputs_id" not in run_space
        ), "inputs_id must not be present at inspection"
        # Only spec_id is allowed
        allowed_keys = {"spec_id"}
        actual_keys = set(run_space.keys())
        assert (
            actual_keys <= allowed_keys
        ), f"run_space contains unexpected keys: {actual_keys - allowed_keys}"


def test_identity_determinism(simple_pipeline_config):
    """Test that identity computation is deterministic across multiple runs."""
    payload1 = build(simple_pipeline_config)
    payload2 = build(simple_pipeline_config)

    identity1 = payload1.get("identity", {})
    identity2 = payload2.get("identity", {})

    assert (
        identity1["semantic_id"] == identity2["semantic_id"]
    ), "semantic_id must be deterministic"
    assert (
        identity1["config_id"] == identity2["config_id"]
    ), "config_id must be deterministic"


def test_sweep_is_sanitized_no_raw_expressions(simple_pipeline_config):
    """Test that sweep metadata contains only sanitized signatures, never raw expressions."""
    payload = build(simple_pipeline_config)
    json.dumps(payload)

    # Raw "expr" field should not appear anywhere in top-level payload
    # (it's allowed in preprocessor_view which is excluded from canonical payloads)
    spec_canonical = payload.get("pipeline_spec_canonical", {})
    spec_json = json.dumps(spec_canonical)

    # In pipeline_spec_canonical, we should only see sanitized signatures
    assert (
        '"expr"' not in spec_json or "expr" not in spec_json
    ), "Raw 'expr' fields must not appear in pipeline_spec_canonical"


def test_payload_structure(simple_pipeline_config):
    """Test that payload has the expected top-level structure."""
    payload = build(simple_pipeline_config)

    # Required top-level keys
    assert "identity" in payload
    assert "pipeline_spec_canonical" in payload
    assert "required_context_keys" in payload

    # pipeline_spec_canonical should have nodes
    spec = payload["pipeline_spec_canonical"]
    assert isinstance(spec, dict)
    assert "nodes" in spec
    assert isinstance(spec["nodes"], list)


def test_node_semantic_id_present(simple_pipeline_config):
    """Test that each node in canonical spec includes node_semantic_id."""
    payload = build(simple_pipeline_config)
    nodes = payload.get("pipeline_spec_canonical", {}).get("nodes", [])

    for idx, node in enumerate(nodes):
        assert "node_semantic_id" in node, f"Node {idx} missing node_semantic_id"
        assert "uuid" in node, f"Node {idx} missing uuid"
        assert "role" in node, f"Node {idx} missing role"
        assert "fqcn" in node, f"Node {idx} missing fqcn"


def test_run_space_spec_id_when_present():
    """Test that run_space.spec_id is computed when run_space is defined."""
    config_with_run_space = {
        "pipeline": {
            "nodes": [
                {
                    "name": "source",
                    "processor": "semantiva.examples.test_utils.IntGenerator",
                    "parameters": {"value": 42},
                }
            ]
        },
        "run_space": {
            "sweep": [
                {"context_key": "value", "values": [1, 2, 3]},
            ]
        },
    }

    payload = build(config_with_run_space)
    identity = payload.get("identity", {})
    run_space = identity.get("run_space")

    assert run_space is not None, "run_space should be present when defined in config"
    assert isinstance(run_space, dict)
    assert "spec_id" in run_space, "spec_id must be present"
    assert run_space["spec_id"] is not None, "spec_id should be computed"
    assert "inputs_id" not in run_space, "inputs_id must not be present"


@pytest.mark.skipif(
    not Path("docs/source/examples/pipeline_sweep_parameters_first.yaml").exists(),
    reason="Example file not found",
)
def test_sweep_example_sanitization():
    """Test that the sweep example file produces sanitized output."""
    import yaml

    yaml_path = Path("docs/source/examples/pipeline_sweep_parameters_first.yaml")
    with yaml_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    payload = build(config)
    payload_json = json.dumps(payload)

    # Should contain signature fields
    assert "parameters_sig" in payload_json, "Sweep should include parameters_sig"
    assert "variables_sig" in payload_json, "Sweep should include variables_sig"

    # Check nodes for sweep metadata
    nodes = payload.get("pipeline_spec_canonical", {}).get("nodes", [])
    sweep_nodes = [
        n
        for n in nodes
        if n.get("preprocessor_metadata", {}).get("derive", {}).get("parameter_sweep")
    ]

    if sweep_nodes:
        for node in sweep_nodes:
            sweep_block = node["preprocessor_metadata"]["derive"]["parameter_sweep"]
            assert "parameters_sig" in sweep_block
            assert "variables_sig" in sweep_block
            assert "mode" in sweep_block
            assert "broadcast" in sweep_block
            assert "collection" in sweep_block
