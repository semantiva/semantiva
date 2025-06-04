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
from semantiva.payload_operations.pipeline_inspector import PipelineInspector
from semantiva.examples.test_utils import FloatMultiplyOperation, FloatCollectValueProbe


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

    inspection_report = PipelineInspector.inspect(pipeline.nodes)
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
