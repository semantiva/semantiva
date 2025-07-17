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
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json
import yaml

from semantiva import Pipeline
from semantiva.tools.serve_pipeline_gui import app, build_pipeline_json
from semantiva.tools.pipeline_inspector import PipelineInspector
from semantiva.examples.test_utils import FloatMultiplyOperation, FloatCollectValueProbe


@pytest.fixture
def test_pipeline():
    """Generate a pipeline for testing."""
    node_configuration = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": FloatMultiplyOperation},
        {"processor": "rename:factor:renamed_key"},
        {"processor": "delete:renamed_key"},
    ]

    return Pipeline(node_configuration)


@pytest.fixture
def test_client(test_pipeline):
    """Create a FastAPI test client with the test pipeline."""
    # Set the global pipeline variable for testing
    app.state.pipeline = test_pipeline

    # Return the test client
    return TestClient(app)


def test_build_pipeline_json(test_pipeline):
    """Test the build_pipeline_json function."""
    # Get the pipeline JSON
    pipeline_json = build_pipeline_json(test_pipeline)

    # Check basic structure
    assert "nodes" in pipeline_json
    assert "edges" in pipeline_json

    # Check nodes
    assert len(pipeline_json["nodes"]) == 4  # Four nodes in our test pipeline

    # Check first node
    first_node = pipeline_json["nodes"][0]
    assert first_node["label"] == "FloatCollectValueProbe"
    assert "parameters" in first_node
    assert "parameter_resolution" in first_node

    # Check edges
    assert len(pipeline_json["edges"]) == 3  # Three edges connecting four nodes
    assert pipeline_json["edges"][0]["source"] == 0
    assert pipeline_json["edges"][0]["target"] == 1


def test_get_pipeline_endpoint(test_client):
    """Test the /pipeline endpoint."""
    # Call the endpoint
    response = test_client.get("/pipeline")

    # Check response
    assert response.status_code == 200

    # Parse JSON response
    data = response.json()

    # Check structure
    assert "nodes" in data
    assert "edges" in data

    # Check that nodes have expected data
    assert len(data["nodes"]) == 4
    assert data["nodes"][0]["label"] == "FloatCollectValueProbe"
    assert data["nodes"][1]["label"] == "FloatMultiplyOperation"


def test_index_endpoint(test_client):
    """Test the / endpoint."""
    response = test_client.get("/")
    assert (
        response.status_code == 200 or response.status_code == 404
    )  # 404 is acceptable if the file doesn't exist in test


def test_debug_endpoint(test_client):
    """Test the /debug endpoint."""
    try:
        response = test_client.get("/debug")
        assert (
            response.status_code == 200 or response.status_code == 404
        )  # 404 is acceptable if the file doesn't exist in test
    except RuntimeError as e:
        # The file doesn't exist, which is also acceptable for the test
        assert "does not exist" in str(e)


def test_pipeline_json_has_parameter_resolution(test_pipeline):
    """Test that the pipeline JSON includes parameter resolution data."""
    # Get the pipeline JSON
    pipeline_json = build_pipeline_json(test_pipeline)

    # Check that each node has parameter resolution data
    for node in pipeline_json["nodes"]:
        assert "parameter_resolution" in node
        if node["label"] == "FloatMultiplyOperation":
            # Check that factor is in the parameter resolution structure
            # It could be directly in parameter_resolution or in from_context
            has_factor = "factor" in node["parameter_resolution"] or (
                "from_context" in node["parameter_resolution"]
                and "factor" in node["parameter_resolution"]["from_context"]
            )
            assert (
                has_factor
            ), f"Expected 'factor' in parameter resolution, found: {node['parameter_resolution']}"
