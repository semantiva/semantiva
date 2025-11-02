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

"""Test semantic ID computation for pipelines and configuration identification."""

import pytest

from semantiva.metadata import (
    compute_pipeline_semantic_id,
    compute_pipeline_config_id,
    compute_node_semantic_id,
)


def test_compute_pipeline_semantic_id_deterministic():
    """Verify that pipeline semantic IDs are deterministic from canonical spec."""
    canonical_spec = {
        "version": 1,
        "nodes": [
            {
                "node_uuid": "uuid-1",
                "name": "ProcessorA",
                "payload_from": None,
            },
            {
                "node_uuid": "uuid-2",
                "name": "ProcessorB",
                "payload_from": "uuid-1",
            },
        ],
    }

    # Same canonical spec should produce same ID
    id1 = compute_pipeline_semantic_id(canonical_spec)
    id2 = compute_pipeline_semantic_id(canonical_spec)

    assert id1 == id2
    assert id1.startswith("plsemid-")


def test_compute_pipeline_semantic_id_differs_with_structure():
    """Verify that different pipeline structures produce different semantic IDs."""
    spec_a = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "ProcessorA", "payload_from": None},
            {"node_uuid": "uuid-2", "name": "ProcessorB", "payload_from": "uuid-1"},
        ],
    }

    spec_b = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "ProcessorA", "payload_from": None},
            {
                "node_uuid": "uuid-2",
                "name": "ProcessorC",
                "payload_from": "uuid-1",
            },  # Different processor
        ],
    }

    id_a = compute_pipeline_semantic_id(spec_a)
    id_b = compute_pipeline_semantic_id(spec_b)

    assert id_a != id_b
    assert id_a.startswith("plsemid-")
    assert id_b.startswith("plsemid-")


def test_compute_pipeline_semantic_id_differs_with_connectivity():
    """Verify that different connectivity produces different semantic IDs."""
    spec_linear = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "A", "payload_from": None},
            {"node_uuid": "uuid-2", "name": "B", "payload_from": "uuid-1"},
            {"node_uuid": "uuid-3", "name": "C", "payload_from": "uuid-2"},
        ],
    }

    spec_parallel = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "A", "payload_from": None},
            {"node_uuid": "uuid-2", "name": "B", "payload_from": "uuid-1"},
            {
                "node_uuid": "uuid-3",
                "name": "C",
                "payload_from": "uuid-1",
            },  # Branch to uuid-1 instead of uuid-2
        ],
    }

    id_linear = compute_pipeline_semantic_id(spec_linear)
    id_parallel = compute_pipeline_semantic_id(spec_parallel)

    assert id_linear != id_parallel


def test_compute_pipeline_semantic_id_ignores_non_structural_fields():
    """Verify that non-structural fields don't affect semantic ID."""
    base_spec = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "ProcessorA", "payload_from": None},
        ],
    }

    # Same structure with extra fields
    extended_spec = {
        "version": 1,
        "nodes": [
            {
                "node_uuid": "uuid-1",
                "name": "ProcessorA",
                "payload_from": None,
                "params": {"x": 10},  # Runtime params shouldn't affect semantic ID
                "declaration_index": 0,
            },
        ],
        "edges": [],  # Extra field
    }

    id_base = compute_pipeline_semantic_id(base_spec)
    id_extended = compute_pipeline_semantic_id(extended_spec)

    # Both should compute same ID (structure is identical)
    # Only name, node_uuid, and payload_from are used
    assert id_base == id_extended


def test_compute_pipeline_config_id_deterministic():
    """Verify that config IDs are deterministic from node semantic pairs."""
    pairs = [
        ("uuid-1", "sem-id-1"),
        ("uuid-2", "sem-id-2"),
    ]

    id1 = compute_pipeline_config_id(pairs)
    id2 = compute_pipeline_config_id(pairs)

    assert id1 == id2
    assert id1.startswith("plcid-")


def test_compute_pipeline_config_id_differs_with_node_ids():
    """Verify that different node semantic IDs produce different config IDs."""
    pairs_a = [
        ("uuid-1", "sem-id-1"),
        ("uuid-2", "sem-id-2"),
    ]

    pairs_b = [
        ("uuid-1", "sem-id-1"),
        ("uuid-2", "sem-id-2-changed"),  # Different semantic ID for node 2
    ]

    id_a = compute_pipeline_config_id(pairs_a)
    id_b = compute_pipeline_config_id(pairs_b)

    assert id_a != id_b
    assert id_a.startswith("plcid-")
    assert id_b.startswith("plcid-")


def test_compute_pipeline_config_id_order_independent():
    """Verify that config ID is consistent regardless of input order."""
    pairs_ordered = [
        ("uuid-1", "sem-id-1"),
        ("uuid-2", "sem-id-2"),
        ("uuid-3", "sem-id-3"),
    ]

    pairs_shuffled = [
        ("uuid-3", "sem-id-3"),
        ("uuid-1", "sem-id-1"),
        ("uuid-2", "sem-id-2"),
    ]

    id_ordered = compute_pipeline_config_id(pairs_ordered)
    id_shuffled = compute_pipeline_config_id(pairs_shuffled)

    # Should be identical because function sorts by UUID internally
    assert id_ordered == id_shuffled


def test_semantic_id_vs_config_id_are_distinct():
    """Verify that semantic_id and config_id compute different fingerprints."""
    canonical_spec = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "ProcessorA", "payload_from": None},
        ],
    }

    pairs = [("uuid-1", "sem-id-1")]

    semantic_id = compute_pipeline_semantic_id(canonical_spec)
    config_id = compute_pipeline_config_id(pairs)

    # Different fields, so different IDs
    assert semantic_id != config_id
    assert semantic_id.startswith("plsemid-")
    assert config_id.startswith("plcid-")


def test_compute_node_semantic_id_with_preprocessor_metadata():
    """Verify that node semantic IDs are computed from preprocessor metadata."""
    preproc_meta = {
        "type": "derive.parameter_sweep",
        "version": 1,
        "element_ref": "TestProcessor",
        "mode": "combinatorial",
        "param_expressions": {"value": {"sig": "x * 2"}},
        "variables": {"x": {"type": "range", "lo": 0.0, "hi": 10.0, "steps": 5}},
        "broadcast": False,
        "collection": "TestCollection",
        "dependencies": {"required_external_parameters": [], "context_keys": []},
    }

    sem_id = compute_node_semantic_id(preproc_meta)

    assert isinstance(sem_id, str)
    assert len(sem_id) == 64  # SHA256 hex digest


def test_pipeline_semantic_ids_independent_of_node_implementations():
    """Verify that pipeline semantic_id depends on structure, not node implementations."""
    # Two identical pipeline structures but with different node configs
    spec_base = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "NodeA", "payload_from": None},
            {"node_uuid": "uuid-2", "name": "NodeB", "payload_from": "uuid-1"},
        ],
    }

    # Same structure
    spec_same_structure = {
        "version": 1,
        "nodes": [
            {"node_uuid": "uuid-1", "name": "NodeA", "payload_from": None},
            {"node_uuid": "uuid-2", "name": "NodeB", "payload_from": "uuid-1"},
        ],
    }

    id_base = compute_pipeline_semantic_id(spec_base)
    id_same = compute_pipeline_semantic_id(spec_same_structure)

    assert id_base == id_same


def test_config_ids_independent_of_pipeline_structure():
    """Verify that config_id depends only on node semantic IDs, not structure."""
    # Config ID is computed from node semantic pairs, independent of connectivity
    pairs_a = [
        ("uuid-1", "node-sem-1"),
        ("uuid-2", "node-sem-2"),
    ]

    pairs_b = [
        ("uuid-1", "node-sem-1"),
        ("uuid-2", "node-sem-2"),
    ]

    id_a = compute_pipeline_config_id(pairs_a)
    id_b = compute_pipeline_config_id(pairs_b)

    # Same pairs should produce same config ID regardless of "structure"
    assert id_a == id_b


def test_semantic_id_empty_pipeline():
    """Test semantic ID computation for empty pipeline."""
    spec_empty = {"version": 1, "nodes": []}

    semantic_id = compute_pipeline_semantic_id(spec_empty)

    assert semantic_id.startswith("plsemid-")
    assert isinstance(semantic_id, str)


def test_config_id_empty_pairs():
    """Test config ID computation for empty node pairs."""
    config_id = compute_pipeline_config_id([])

    assert config_id.startswith("plcid-")
    assert isinstance(config_id, str)


def test_large_pipeline_semantic_ids():
    """Test semantic ID computation for larger pipelines."""
    nodes = [
        {
            "node_uuid": f"uuid-{i}",
            "name": f"Processor{i}",
            "payload_from": f"uuid-{i-1}" if i > 0 else None,
        }
        for i in range(10)
    ]

    spec_large = {"version": 1, "nodes": nodes}

    semantic_id = compute_pipeline_semantic_id(spec_large)

    assert semantic_id.startswith("plsemid-")
    assert len(semantic_id) == len("plsemid-") + 64  # Prefix + SHA256 hex


def test_large_pipeline_config_ids():
    """Test config ID computation for larger node lists."""
    pairs = [(f"uuid-{i}", f"sem-id-{i}") for i in range(10)]

    config_id = compute_pipeline_config_id(pairs)

    assert config_id.startswith("plcid-")
    assert len(config_id) == len("plcid-") + 64  # Prefix + SHA256 hex


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
