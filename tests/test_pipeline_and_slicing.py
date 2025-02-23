import pytest
from semantiva.context_operations.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.payload_operations import Pipeline
from .test_utils import (
    FloatDataType,
    FloatDataCollection,
    FloatMultiplyAlgorithm,
    FloatCollectValueProbe,
    FloatCollectionSumAlgorithm,
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
    same size as the number of elements in IntDataCollection."""

    return ContextCollectionType(
        context_list=[ContextType(), ContextType(), ContextType()]
    )


def test_pipeline_execution(float_data, empty_context):
    """Test the execution of a pipeline with multiple nodes."""
    # Define node configurations
    node_configurations = [
        {
            "operation": FloatMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": FloatMultiplyAlgorithm,
            "parameters": {"factor": 3},
        },
        {
            "operation": FloatCollectValueProbe,
        },
        {
            "operation": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": FloatCollectValueProbe,
            "context_keyword": "dummy_keyword",
        },
        {
            "operation": "rename:mock_keyword:final_keyword",
        },
        {
            "operation": "delete:dummy_keyword",
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
            "operation": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": FloatCollectValueProbe,
        },
        {
            "operation": FloatMultiplyAlgorithm,
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
    assert pipeline.get_probe_results()["Node 2/FloatCollectValueProbe"][0] == [
        1.0,
        2.0,
        3.0,
    ]


def test_pipeline_execution_inverted_order(float_data_collection, empty_context):
    """Test the execution of a pipeline with multiple nodes in inverted order.
    The FloatDataCollection is sliced into individual FloatDataType objects,
    and the same context is passed to each sliced item.
    The FloatCollectionSumAlgorithm should sum the values of the FloatDataType objects.
    The final output should be a FloatDataType instance with the sum of the values of the FloatDataType objects.
    The context should remain a single ContextType instance."""
    # Define node configurations
    node_configurations = [
        {
            "operation": FloatMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": FloatCollectValueProbe,
        },
        {
            "operation": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": "rename:mock_keyword:final_keyword",
        },
        {
            "operation": FloatCollectionSumAlgorithm,
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
    assert pipeline.get_probe_results()["Node 2/FloatCollectValueProbe"][0] == [
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
            "operation": FloatMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": FloatCollectValueProbe,
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
        assert "mock_keyword" in context.keys()
        assert context.get_value("mock_keyword") == expected_context_values[i]

    assert (
        pipeline.get_probe_results()["Node 3/FloatCollectValueProbe"][0]
        == expected_context_values
    )


def test_image_pipeline_invalid_configuration():
    """
    Test that an invalid pipeline configuration raises an AssertionError.
    """

    # Define invalid node configurations
    node_configurations = [
        {
            "operation": FloatMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": HelloOperation,
        },
    ]

    # Check that initializing the pipeline raises an AssertionError
    with pytest.raises(AssertionError):
        _ = Pipeline(node_configurations)
