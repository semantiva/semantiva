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

"""Tests for the Pipeline Inspection System.

This test suite validates the new modular inspection architecture including:
- Error-resilient inspection building
- Multiple report format generation
- Parameter origin tracking and resolution
- Validation of invalid configurations
- Integration between builder, reporter, and validator components
"""

import pytest

from semantiva import Pipeline
from semantiva.inspection import (
    build_pipeline_inspection,
    summary_report,
    extended_report,
    json_report,
    parameter_resolutions,
)
from semantiva.inspection.validator import validate_pipeline
from semantiva.exceptions import PipelineConfigurationError
from semantiva.examples.test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
)


@pytest.fixture
def pipeline():
    """Create a test pipeline with context operations for inspection testing.

    This pipeline demonstrates:
    - Context injection (FloatCollectValueProbe adds 'factor' to context)
    - Context consumption (FloatMultiplyOperation uses 'factor' from context)
    - Context manipulation (rename and delete operations)
    """
    node_configuration = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": FloatMultiplyOperation},
        {"processor": "rename:factor:renamed_key"},
        {"processor": "delete:renamed_key"},
    ]
    return Pipeline(node_configuration)


def test_summary_report(pipeline):
    """Test that summary report contains key pipeline structure information."""
    inspection = build_pipeline_inspection(pipeline.pipeline_configuration)
    report = summary_report(inspection)
    assert "Pipeline Structure:" in report
    assert "FloatCollectValueProbe" in report
    assert "Context additions: factor" in report


def test_extended_report(pipeline):
    """Test that extended report includes detailed documentation."""
    inspection = build_pipeline_inspection(pipeline.pipeline_configuration)
    report = extended_report(inspection)
    assert report.startswith("Extended Pipeline Inspection:")
    assert "Footnotes:" in report


def test_json_report(pipeline):
    """Test that JSON report provides structured data for web interfaces."""
    inspection = build_pipeline_inspection(pipeline.pipeline_configuration)
    data = json_report(inspection)
    assert len(data["nodes"]) == 4
    assert data["nodes"][0]["label"] == "FloatCollectValueProbe"


def test_parameter_resolutions(pipeline):
    """Test parameter origin tracking across pipeline nodes."""
    inspection = build_pipeline_inspection(pipeline.pipeline_configuration)
    resolutions = parameter_resolutions(inspection)

    # Second node (FloatMultiplyOperation) should resolve 'factor' from first node
    multiply_node = resolutions[1]
    assert (
        multiply_node["parameter_resolution"]["from_context"]["factor"]["source_idx"]
        == 1
    )


def test_builder_records_errors_and_validator_raises():
    """Test that inspection captures errors while validation can raise them.

    This test demonstrates the error-resilient design:
    1. Inspection succeeds even with invalid configuration
    2. Errors are captured in inspection data structure
    3. Validator can be used separately to raise exceptions when needed
    """
    # Create invalid config: delete 'factor' then try to use it
    config = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": "delete:factor"},  # Delete the factor
        {"processor": FloatMultiplyOperation},  # This needs factor - should error
    ]

    # Build inspection directly from config (this should succeed even with invalid config)
    inspection = build_pipeline_inspection(config)
    assert inspection.nodes[2].errors  # Third node should have error about deleted key

    # Validator should raise exception based on captured errors
    with pytest.raises(PipelineConfigurationError):
        validate_pipeline(inspection)
