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
from semantiva.data_processors.data_slicer_factory import slice
from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.pipeline import Pipeline, Payload
from semantiva.examples.test_utils import (
    FloatDataType,
    FloatDataCollection,
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatCollectionSumOperation,
    FloatValueDataSourceWithDefault,
    FloatMockDataSink,
)
import yaml
from .test_string_extension import HelloOperation


# Start test
@pytest.fixture
def float_data():
    """Pytest fixture for providing an FloatDataType instance with generated floating point data."""
    return FloatDataType(5.0)


@pytest.fixture
def float_data_collection():
    """Pytest fixture for providing an FloatDataCollection instance with generated floating point data."""
    return FloatDataCollection.from_list(
        [FloatDataType(1.0), FloatDataType(2.0), FloatDataType(3.0)]
    )


@pytest.fixture
def empty_context():
    """Pytest fixture for providing an empty context."""
    return ContextType()


@pytest.fixture
def empty_context_collection():
    """Pytest fixture for providing an empty context collection with the
    same size as the number of elements in FloatDataCollection."""

    return ContextCollectionType(
        context_list=[ContextType(), ContextType(), ContextType()]
    )


def test_pipeline_execution(float_data, empty_context):
    """Test the execution of a pipeline with multiple nodes."""
    # Define node configurations
    node_configurations = [
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 3},
        },
        {
            "processor": FloatCollectValueProbe,
            "context_key": "initial_probe",
        },
        {
            "processor": FloatCollectValueProbe,
            "context_key": "mock_keyword",
        },
        {
            "processor": FloatCollectValueProbe,
            "context_key": "dummy_keyword",
        },
        {
            "processor": "rename:mock_keyword:final_keyword",
        },
        {
            "processor": "delete:dummy_keyword",
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    payload = pipeline.process(Payload(float_data, empty_context))
    data, context = payload.data, payload.context

    assert "final_keyword" in context.keys()
    assert context.get_value("final_keyword") == 30
    assert "dummy_keyword" not in context.keys()
    assert context.get_value("initial_probe") == 30.0
    assert "mock_keyword" not in context.keys()
    assert isinstance(data, FloatDataType)
    assert data.data == 30.0


def test_pipeline_execution_with_single_context(float_data_collection, empty_context):
    """Test the execution of a pipeline with single context.
    The FloatDataCollection is sliced into individual FloatDataType objects,
    and the same context is passed to each sliced item.
    The final output should be a FloatDataCollection with the same number of elements as the input collection.
    The context should remain a single ContextType instance."""
    # Define node configurations
    node_configurations = [
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "mock_keyword",
        },
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "probe_slice_secondary",
        },
        {
            "processor": slice(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    payload = pipeline.process(Payload(float_data_collection, empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3
    assert data.data[0].data == 2
    assert data.data[1].data == 4
    assert data.data[2].data == 6
    assert isinstance(context, ContextType)
    assert context.get_value("mock_keyword") == [1.0, 2.0, 3.0]
    assert context.get_value("probe_slice_secondary") == [1.0, 2.0, 3.0]


def test_pipeline_execution_inverted_order(float_data_collection, empty_context):
    """Test the execution of a pipeline with multiple nodes in inverted order.
    The FloatDataCollection is sliced into individual FloatDataType objects,
    and the same context is passed to each sliced item.
    The FloatCollectionSumOperation should sum the values of the FloatDataType objects.
    The final output should be a FloatDataType instance with the sum of the values of the FloatDataType objects.
    The context should remain a single ContextType instance."""
    # Define node configurations
    node_configurations = [
        {
            "processor": slice(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "probe_slice_secondary",
        },
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "mock_keyword",
        },
        {
            "processor": "rename:mock_keyword:final_keyword",
        },
        {
            "processor": FloatCollectionSumOperation,
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    payload = pipeline.process(Payload(float_data_collection, empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataType)
    assert data.data == 12.0
    assert isinstance(context, ContextType)
    assert "final_keyword" in context.keys()
    assert context.get_value("final_keyword") == [2.0, 4.0, 6.0]
    assert context.get_value("probe_slice_secondary") == [2.0, 4.0, 6.0]


def test_pipeline_slicing_with_context_collection(
    float_data_collection, empty_context_collection
):
    """Test the execution of a pipeline with slicing and context collection.
    The FloatDataCollection is sliced into individual FloatDataType objects, and the context collection
    is sliced into individual ContextType objects. The final output should be a FloatDataCollection
    with the same number of elements as the input collection."""
    # Define node configurations
    node_configurations = [
        {
            "processor": slice(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "mock_keyword",
        },
        {
            "processor": slice(FloatCollectValueProbe, FloatDataCollection),
            "context_key": "probe_slice_secondary",
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    payload = pipeline.process(Payload(float_data_collection, empty_context_collection))
    data, context = payload.data, payload.context
    print(context)
    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3
    assert data.data[0].data == 2.0
    assert data.data[1].data == 4.0
    assert data.data[2].data == 6.0
    expected_context_values = [2.0, 4.0, 6.0]
    for i, context in enumerate(context):
        assert context.get_value("mock_keyword") == expected_context_values[i]
        assert context.get_value("probe_slice_secondary") == expected_context_values[i]


def test_yaml_slice_prefix(float_data_collection, empty_context):
    """Test loading a slice-defined processor from YAML configuration."""

    yaml_config = """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "slice:FloatMultiplyOperation:FloatDataCollection"
      parameters:
        factor: 2
"""

    from semantiva.configurations.load_pipeline_from_yaml import parse_pipeline_config

    full_config = yaml.safe_load(yaml_config)
    pipeline_config = parse_pipeline_config(full_config)

    pipeline = Pipeline(pipeline_config.nodes)

    payload = pipeline.process(Payload(float_data_collection, empty_context))

    assert (
        pipeline.nodes[0].processor.__class__.__name__
        == "SlicerForFloatMultiplyOperation"
    )
    data, _ = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert [item.data for item in data] == [2.0, 4.0, 6.0]


def test_image_pipeline_invalid_configuration(empty_context):
    """
    Test that an invalid pipeline configuration raises an AssertionError.
    """

    # Define invalid node configurations
    node_configurations = [
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": HelloOperation,
        },
    ]

    # Check that pipeline execution raises an error
    with pytest.raises(TypeError):
        Pipeline(node_configurations).process(
            Payload(FloatDataType(1.0), empty_context)
        )


def test_data_io_node():
    """Test the execution of a pipeline with a data IO node."""
    # Define node configurations
    node_configurations = [
        {
            "processor": FloatValueDataSourceWithDefault,
        },
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": FloatMockDataSink,
            "parameters": {"path": "mock_file.txt"},
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    payload = pipeline.process()
    data, _ = payload.data, payload.context

    assert data.data == FloatValueDataSourceWithDefault().get_data().data * 2.0
