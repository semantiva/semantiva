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

"""Test that meta dict is captured and preserved in trace aggregation."""

from semantiva.trace.aggregation import TraceAggregator


def test_meta_captured_in_pipeline_start():
    """Verify that the meta dict from pipeline_start is captured in RunAggregate."""
    agg = TraceAggregator()

    # Simulate a pipeline_start record with meta containing semantic IDs
    pipeline_start_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-test-123",
        "pipeline_id": "plid-abc123",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-1",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "TestProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                }
            ],
            "edges": [],
        },
        "meta": {
            "num_nodes": 1,
            "pipeline_config_id": "cfg-xyz789",
            "node_semantic_ids": {
                "node-uuid-1": "sem-id-abc",
            },
        },
    }

    agg.ingest(pipeline_start_record)

    run = agg.get_run("run-test-123")
    assert run is not None
    assert run.meta is not None
    assert run.meta["pipeline_config_id"] == "cfg-xyz789"
    assert run.meta["node_semantic_ids"] == {"node-uuid-1": "sem-id-abc"}
    assert run.meta["num_nodes"] == 1


def test_preprocessor_metadata_in_canonical_spec():
    """Verify that preprocessor_metadata can be included in canonical spec nodes."""
    agg = TraceAggregator()

    preprocessor_meta = {
        "type": "derive.parameter_sweep",
        "version": 1,
        "element_ref": "TestProcessor",
        "param_expressions": {"value": {"sig": "x * 2"}},
        "variables": {"x": {"type": "range", "lo": 0.0, "hi": 10.0, "steps": 5}},
        "mode": "combinatorial",
        "broadcast": False,
        "collection": "TestCollection",
        "dependencies": {
            "required_external_parameters": [],
            "context_keys": [],
        },
    }

    pipeline_start_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-test-456",
        "pipeline_id": "plid-def456",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-2",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "TestSweepProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                    "preprocessor_metadata": preprocessor_meta,
                }
            ],
            "edges": [],
        },
        "meta": {
            "num_nodes": 1,
            "pipeline_config_id": "cfg-sweep-123",
            "node_semantic_ids": {
                "node-uuid-2": "sem-id-sweep-abc",
            },
        },
    }

    agg.ingest(pipeline_start_record)

    run = agg.get_run("run-test-456")
    assert run is not None
    assert run.pipeline_spec_canonical is not None

    # Verify preprocessor_metadata is preserved in canonical spec
    nodes = run.pipeline_spec_canonical.get("nodes", [])
    assert len(nodes) == 1
    assert "preprocessor_metadata" in nodes[0]
    assert nodes[0]["preprocessor_metadata"]["type"] == "derive.parameter_sweep"
    assert "param_expressions" in nodes[0]["preprocessor_metadata"]
    assert "value" in nodes[0]["preprocessor_metadata"]["param_expressions"]


def test_missing_fields_are_optional():
    """Test that meta and preprocessor_metadata fields are optional."""
    agg = TraceAggregator()

    # Old trace without meta field
    pipeline_start_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-no-meta",
        "pipeline_id": "plid-no-meta",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-1",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "BasicProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                    # No preprocessor_metadata (non-sweep node)
                }
            ],
            "edges": [],
        },
        # No meta field
    }

    agg.ingest(pipeline_start_record)

    run = agg.get_run("run-no-meta")
    assert run is not None
    assert run.meta is None  # Missing meta is acceptable
    assert "preprocessor_metadata" not in run.pipeline_spec_canonical["nodes"][0]


def test_semantic_id_and_config_id_captured():
    """Verify that both semantic_id and config_id are captured in meta dict."""
    agg = TraceAggregator()

    pipeline_start_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-with-ids",
        "pipeline_id": "plid-with-ids",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-1",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "TestProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                }
            ],
            "edges": [],
        },
        "meta": {
            "num_nodes": 1,
            "semantic_id": "plsemid-abcdef0123456789",
            "config_id": "plcid-xyz789abcdef0123456789",
            "node_semantic_ids": {
                "node-uuid-1": "sem-id-node1",
            },
        },
    }

    agg.ingest(pipeline_start_record)

    run = agg.get_run("run-with-ids")
    assert run is not None
    assert run.meta is not None
    assert "semantic_id" in run.meta
    assert "config_id" in run.meta
    assert run.meta["semantic_id"] == "plsemid-abcdef0123456789"
    assert run.meta["config_id"] == "plcid-xyz789abcdef0123456789"
    assert run.meta["node_semantic_ids"]["node-uuid-1"] == "sem-id-node1"


def test_semantic_id_and_config_id_are_distinct():
    """Verify that semantic_id and config_id are different values."""
    agg = TraceAggregator()

    pipeline_start_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-distinct-ids",
        "pipeline_id": "plid-distinct",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-1",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "TestProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                }
            ],
            "edges": [],
        },
        "meta": {
            "num_nodes": 1,
            "semantic_id": "plsemid-structure-hash-123",
            "config_id": "plcid-config-hash-789",
            "node_semantic_ids": {
                "node-uuid-1": "sem-id-1",
            },
        },
    }

    agg.ingest(pipeline_start_record)

    run = agg.get_run("run-distinct-ids")
    assert run.meta["semantic_id"] != run.meta["config_id"]
    assert run.meta["semantic_id"].startswith("plsemid-")
    assert run.meta["config_id"].startswith("plcid-")


def test_semantic_id_config_id_backward_compatibility():
    """Test that old traces with only pipeline_config_id still work."""
    agg = TraceAggregator()

    # Old format with only pipeline_config_id
    old_record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "timestamp": "2025-11-02T10:00:00.000Z",
        "seq": 1,
        "run_id": "run-old-format",
        "pipeline_id": "plid-old",
        "pipeline_spec_canonical": {
            "version": 1,
            "nodes": [
                {
                    "node_uuid": "node-uuid-1",
                    "declaration_index": 0,
                    "declaration_subindex": 0,
                    "processor_ref": "TestProcessor",
                    "role": "processor",
                    "params": {},
                    "ports": {},
                }
            ],
            "edges": [],
        },
        "meta": {
            "num_nodes": 1,
            "pipeline_config_id": "old-config-id-123",  # Old field name
            "node_semantic_ids": {
                "node-uuid-1": "sem-id-old",
            },
        },
    }

    agg.ingest(old_record)

    run = agg.get_run("run-old-format")
    assert run is not None
    assert run.meta is not None
    assert "pipeline_config_id" in run.meta  # Still preserved for compatibility
