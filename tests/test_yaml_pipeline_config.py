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
from pathlib import Path

from semantiva import Pipeline, load_pipeline_from_yaml, Payload
from semantiva.examples.test_utils import FloatDataType
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType


def test_load_pipeline_from_yaml():
    """Test loading and executing a pipeline from YAML configuration."""

    # Get the path to the test pipeline config
    test_dir = Path(__file__).parent
    yaml_file = test_dir / "pipeline_config.yaml"

    # Ensure the YAML file exists
    assert yaml_file.exists(), f"Pipeline config file not found: {yaml_file}"

    # Load the pipeline configuration from YAML
    node_configurations = load_pipeline_from_yaml(str(yaml_file))

    # Verify the configuration was loaded properly
    assert isinstance(node_configurations, list), "Configuration should be a list"
    assert len(node_configurations) > 0, "Configuration should not be empty"

    # Check that the first node is our FloatMockDataSource
    assert node_configurations[0]["processor"] == "FloatMockDataSource"

    # Create and execute the pipeline
    pipeline = Pipeline(node_configurations)

    # Process the pipeline (no initial data needed since we start with DataSource)
    payload = pipeline.process()
    data, context = payload.data, payload.context

    # Verify the output
    assert isinstance(data, FloatDataType), "Output should be FloatDataType"
    assert isinstance(context, ContextType), "Context should be ContextType"

    # Verify context contains expected keys
    assert "final_value" in context.keys(), "Context should contain 'final_value'"
    assert (
        "initial_float" not in context.keys()
    ), "Context should not contain deleted key 'initial_float'"

    # Verify the mathematical pipeline progression
    # Starting value from FloatMockDataSource: 42.0
    # FloatCollectValueProbe: collects 42.0 as "initial_float"
    # rename:initial_float:addend: renames "initial_float" to "addend" (value still 42.0)
    # After FloatMultiplyOperation (factor=2.5): 42.0 * 2.5 = 105.0
    # After FloatSquareOperation: 105.0 ** 2 = 11025.0
    # After FloatAddOperation (addend=42.0): 11025.0 + 42.0 = 11067.0
    # After FloatSqrtOperation: sqrt(11067.0) ≈ 105.20
    # After FloatDivideOperation (divisor=3.0): 105.20 / 3.0 ≈ 35.067

    import math

    step1 = 42.0  # Initial value
    step2 = step1 * 2.5  # Multiply: 105.0
    step3 = step2**2  # Square: 11025.0
    step4 = step3 + step1  # Add (addend=initial_value): 11067.0
    step5 = math.sqrt(step4)  # Sqrt: ~105.20
    expected_final_value = step5 / 3.0  # Divide: ~35.067
    assert (
        abs(data.data - expected_final_value) < 0.001
    ), f"Expected {expected_final_value}, got {data.data}"

    # Verify the context value matches what was collected
    collected_value = context.get_value("final_value").get("value", None)
    # This should be the final computed value (same as expected_final_value)
    assert (
        abs(collected_value - expected_final_value) < 0.001
    ), f"Expected context value {expected_final_value}, got {collected_value}"


def test_yaml_configuration_validation():
    """Test that YAML configuration validation works correctly."""

    # Test with invalid YAML content
    invalid_yaml_content = """
invalid_structure:
  missing_pipeline_key: true
"""

    # Create a temporary invalid YAML file
    test_dir = Path(__file__).parent
    invalid_yaml_file = test_dir / "invalid_pipeline_config.yaml"

    try:
        with open(invalid_yaml_file, "w") as f:
            f.write(invalid_yaml_content)

        # This should raise a ValueError due to missing 'pipeline' key
        with pytest.raises(ValueError, match="Invalid pipeline configuration"):
            load_pipeline_from_yaml(str(invalid_yaml_file))

    finally:
        # Clean up the temporary file
        if invalid_yaml_file.exists():
            invalid_yaml_file.unlink()


def test_yaml_string_class_resolution():
    """Test that string class names in YAML are properly resolved to actual classes."""

    test_dir = Path(__file__).parent
    yaml_file = test_dir / "pipeline_config.yaml"

    # Load configuration
    node_configurations = load_pipeline_from_yaml(str(yaml_file))

    # Create pipeline and run once to instantiate nodes
    pipeline = Pipeline(node_configurations)
    pipeline.process(Payload(NoDataType(), ContextType()))

    # Verify that the pipeline nodes were created successfully
    assert len(pipeline.nodes) > 0, "Pipeline should have nodes"

    # Check that string processors were resolved to actual classes
    for i, node_config in enumerate(node_configurations):
        processor = node_config["processor"]
        if isinstance(processor, str):
            node = pipeline.nodes[i]
            assert hasattr(
                node, "processor"
            ), f"Node {i} should have a processor attribute"
