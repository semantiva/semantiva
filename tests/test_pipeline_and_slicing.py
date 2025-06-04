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
from semantiva.data_processors.data_slicer_factory import Slicer
from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.exceptions.pipeline import PipelineTopologyError
from semantiva.payload_operations import Pipeline
from semantiva.examples.test_utils import (
    FloatDataType,
    FloatDataCollection,
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatCollectionSumOperation,
    FloatMockDataSource,
    FloatMockDataSink,
)
from .test_string_specialization import HelloOperation


# Start test
@pytest.fixture
def float_data():
    """Pytest fixture for providing an FloatDataType instance with generated integer data."""
    return FloatDataType(5.0)


@pytest.fixture
def float_data_collection():
    """Pytest fixture for providing an FloatDataCollection instance with generated integer data."""
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
        },
        {
            "processor": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "processor": FloatCollectValueProbe,
            "context_keyword": "dummy_keyword",
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
    data, context = pipeline.process(float_data, empty_context)

    assert "final_keyword" in context.keys()
    assert context.get_value("final_keyword") == 30
    assert "dummy_keyword" not in context.keys()
    assert isinstance(data, FloatDataType)
    assert data.data == 30.0
    assert pipeline.get_probe_results()["Node 3/FloatCollectValueProbe"][0] == 30.0


def test_pipeline_execution_with_single_context(float_data_collection, empty_context):
    """Test the execution of a pipeline with single context.
    The FloatDataCollection is sliced into individual FloatDataType objects,
    and the same context is passed to each sliced item.
    The final output should be a FloatDataCollection with the same number of elements as the input collection.
    The context should remain a single ContextType instance."""
    # Define node configurations
    node_configurations = [
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
            "context_keyword": "mock_keyword",
        },
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
        },
        {
            "processor": Slicer(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    data, context = pipeline.process(float_data_collection, empty_context)

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3
    assert data.data[0].data == 2
    assert data.data[1].data == 4
    assert data.data[2].data == 6
    assert isinstance(context, ContextType)
    assert context.get_value("mock_keyword") == [1.0, 2.0, 3.0]
    assert pipeline.get_probe_results()["Node 2/SlicerForFloatCollectValueProbe"][
        0
    ] == [
        1.0,
        2.0,
        3.0,
    ]


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
            "processor": Slicer(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
        },
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
            "context_keyword": "mock_keyword",
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
    data, context = pipeline.process(float_data_collection, empty_context)

    assert isinstance(data, FloatDataType)
    assert data.data == 12.0
    assert isinstance(context, ContextType)
    assert "final_keyword" in context.keys()
    assert context.get_value("final_keyword") == [2.0, 4.0, 6.0]
    assert pipeline.get_probe_results()["Node 2/SlicerForFloatCollectValueProbe"][
        0
    ] == [
        2.0,
        4.0,
        6.0,
    ]


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
            "processor": Slicer(FloatMultiplyOperation, FloatDataCollection),
            "parameters": {"factor": 2},
        },
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
            "context_keyword": "mock_keyword",
        },
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    data, context = pipeline.process(float_data_collection, empty_context_collection)
    print(context)
    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3
    assert data.data[0].data == 2.0
    assert data.data[1].data == 4.0
    assert data.data[2].data == 6.0
    expected_context_values = [2.0, 4.0, 6.0]
    for i, context in enumerate(context):
        assert context.get_value("mock_keyword") == expected_context_values[i]

    assert (
        pipeline.get_probe_results()["Node 3/SlicerForFloatCollectValueProbe"][0]
        == expected_context_values
    )


def test_image_pipeline_invalid_configuration():
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

    # Check that initializing the pipeline raises an AssertionError
    with pytest.raises(PipelineTopologyError):
        _ = Pipeline(node_configurations)


def test_data_io_node():
    """Test the execution of a pipeline with a data IO node."""
    # Define node configurations
    node_configurations = [
        {
            "processor": FloatMockDataSource,
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
    data, context = pipeline.process()

    assert data.data == FloatMockDataSource().get_data().data * 2.0
