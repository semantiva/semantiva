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

import pytest

from semantiva.payload_operations.pipeline import Pipeline
from semantiva.tools.pipeline_inspector import PipelineInspector
from semantiva.examples.test_utils import FloatMultiplyOperation, FloatCollectValueProbe
from semantiva.exceptions.pipeline import PipelineConfigurationError


@pytest.fixture
def pipeline():
    """Generate a pipeline for testing."""
    node_configuration = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": FloatMultiplyOperation},
        {"processor": "rename:factor:renamed_key"},
        {"processor": "delete:renamed_key"},
    ]

    pipeline = Pipeline(node_configuration)
    return pipeline


def test_pipeline_inspector(pipeline):
    """Test the pipeline inspector."""

    inspection_report = PipelineInspector.inspect_pipeline(pipeline)
    print(inspection_report)
    # Check if the report contains expected information
    assert "Pipeline Structure:" in inspection_report
    assert "Required context keys:" in inspection_report
    assert "FloatCollectValueProbe" in inspection_report
    assert "FloatMultiplyOperation" in inspection_report
    assert "Context additions: factor" in inspection_report
    assert "From context: factor (from Node 1)" in inspection_report
    assert "Context additions: renamed_key" in inspection_report
    assert "Context suppressions: factor" in inspection_report
    assert "Required context keys: None" in inspection_report
    assert "Context suppressions: renamed_key" in inspection_report


def test_inspect_config_equivalence(pipeline):
    """
    The inspect_config method should produce the same report as inspect_pipeline.
    """
    # Use raw configuration to inspect via inspect_config
    config = pipeline.pipeline_configuration
    report_from_config = PipelineInspector.inspect_config(config)
    # Inspect using the existing pipeline instance
    report_from_pipeline = PipelineInspector.inspect_pipeline(pipeline)
    assert report_from_config == report_from_pipeline


def test_format_set_empty_and_non_empty():
    assert PipelineInspector._format_set([]) == "None"
    assert PipelineInspector._format_set(set()) == "None"
    assert PipelineInspector._format_set(["b", "a"]) == "a, b"
    assert PipelineInspector._format_set({"x", "y"}) in ("x, y", "y, x")


def test_format_pipeline_config():
    assert PipelineInspector._format_pipeline_config({}) == "None"
    cfg = {"a": 1, "b": 2}
    result = PipelineInspector._format_pipeline_config(cfg)
    assert result == "a=1, b=2"


def test_format_context_params():
    # empty context
    assert PipelineInspector._format_context_params(set(), {}) == "None"
    # with origins
    context_params = {"foo", "bar"}
    key_origin = {"foo": 1}
    out = PipelineInspector._format_context_params(context_params, key_origin)
    # 'bar' no origin, 'foo' from Node 1
    assert "bar" in out and "foo (from Node 1)" in out


def test_inspect_pipeline_extended(pipeline):
    report = PipelineInspector.inspect_pipeline_extended(pipeline)
    # Basic assertions
    assert report.startswith("Extended Pipeline Inspection:")
    # Footnotes section
    assert "Footnotes:" in report
    # Ensure processor docstring is present as a footnote
    assert "FloatCollectValueProbe" in report


def test_inspect_config_extended_equivalence(pipeline):
    cfg = pipeline.pipeline_configuration
    rpt1 = PipelineInspector.inspect_config_extended(cfg)
    rpt2 = PipelineInspector.inspect_pipeline_extended(pipeline)
    assert rpt1 == rpt2


def test_get_nodes_semantic_ids_report(pipeline):
    nodes = pipeline.nodes
    rpt = PipelineInspector.get_nodes_semantic_ids_report(nodes)
    # Should start with first node
    assert rpt.startswith(f"\nNode 1:\n{nodes[0].semantic_id()}")
    # Should contain entries for all nodes
    for i, node in enumerate(nodes, start=1):
        assert f"Node {i}:" in rpt
        assert node.semantic_id() in rpt


def test_validate_deleted_keys_error_and_ok():
    # Case: missing_deleted_keys not restored -> error
    with pytest.raises(PipelineConfigurationError):
        PipelineInspector._validate_deleted_keys(
            index=3, operation_params={"foo"}, config_params=set(), deleted_keys={"foo"}
        )
    # Case: restored via config -> no error
    PipelineInspector._validate_deleted_keys(
        index=3, operation_params={"foo"}, config_params={"foo"}, deleted_keys={"foo"}
    )
