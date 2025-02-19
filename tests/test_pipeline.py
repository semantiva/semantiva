import pytest
from semantiva.context_operations.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.payload_operations import Pipeline
from .test_utils import (
    IntDataType,
    IntDataCollection,
    IntMultiplyAlgorithm,
    IntCollectValueProbe,
    IntCollectionSumAlgorithm,
)


# Start test
@pytest.fixture
def int_data():
    """Pytest fixture for providing an IntDataType instance with generated integer data."""
    return IntDataType(5)


@pytest.fixture
def int_data_collection():
    """Pytest fixture for providing an IntDataCollection instance with generated integer data."""
    return IntDataCollection.from_list([IntDataType(1), IntDataType(2), IntDataType(3)])


@pytest.fixture
def empty_context():
    """Pytest fixture for providing an empty context."""
    return ContextType()


@pytest.fixture
def empty_context_collection():
    """Pytest fixture for providing an empty context collection with the
    same size as the number of elements in IntDataCollection."""

    return ContextCollectionType([ContextType(), ContextType(), ContextType()])


def test_pipeline_execution(int_data, empty_context):
    """Test the execution of a pipeline with multiple nodes."""
    # Define node configurations
    node_configurations = [
        {
            "operation": IntMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": IntMultiplyAlgorithm,
            "parameters": {"factor": 3},
        },
        {
            "operation": IntCollectValueProbe,
        },
        {
            "operation": IntCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": IntCollectValueProbe,
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
    data, context = pipeline.process(int_data, empty_context)

    assert "final_keyword" in context.keys()
    assert context.get_value("final_keyword") == 30
    assert "dummy_keyword" not in context.keys()
    assert isinstance(data, IntDataType)
    assert data.data == 30
    assert pipeline.get_probe_results()["Node 3/IntCollectValueProbe"][0] == 30


def test_pipeline_execution_with_collection(int_data_collection, empty_context):
    """Test the execution of a pipeline with collection data."""
    # Define node configurations
    node_configurations = [
        {
            "operation": IntCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": IntCollectValueProbe,
        },
        {
            "operation": IntCollectionSumAlgorithm,
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    # Process the data
    data, context = pipeline.process(int_data_collection, empty_context)

    assert isinstance(data, IntDataType)
    assert data.data == 6
    assert context.get_value("mock_keyword") == [1, 2, 3]
    assert pipeline.get_probe_results()["Node 2/IntCollectValueProbe"][0] == [1, 2, 3]


def test_pipeline_slicing(int_data_collection, empty_context_collection):
    """Test the execution of a pipeline with slicing."""
    # Define node configurations
    node_configurations = [
        {
            "operation": IntMultiplyAlgorithm,
            "parameters": {"factor": 2},
        },
        {
            "operation": IntCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": IntCollectValueProbe,
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)

    data, context = pipeline.process(int_data_collection, empty_context_collection)
    print(context)
    assert isinstance(data, IntDataCollection)
    assert len(data) == 3
    assert data.data[0].data == 2
    assert data.data[1].data == 4
    assert data.data[2].data == 6
    expected_context_values = [2, 4, 6]
    for i, context in enumerate(context):
        assert "mock_keyword" in context.keys()
        assert context.get_value("mock_keyword") == expected_context_values[i]

    assert (
        pipeline.get_probe_results()["Node 3/IntCollectValueProbe"][0]
        == expected_context_values
    )
