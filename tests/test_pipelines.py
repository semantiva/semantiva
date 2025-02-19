import pytest
from semantiva.data_types.data_types import BaseDataType, DataCollectionType
from semantiva.context_operations.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.data_operations import DataAlgorithm, DataProbe
from semantiva.payload_operations import Pipeline


# Concrete implementation of BaseDataType for testing
class IntDataType(BaseDataType[int]):
    """A data type for integers."""

    def validate(self, data: int) -> bool:
        if not isinstance(data, int):
            raise TypeError("Data must be an integer")
        return True


# Concrete implementation of DataCollectionType for testing
class IntDataCollection(DataCollectionType[IntDataType, list]):
    """A collection of IntDataType objects."""

    @classmethod
    def _initialize_empty(cls) -> list:
        return []

    def __iter__(self):
        return iter(self._data)

    def append(self, item: IntDataType) -> None:
        if not isinstance(item, IntDataType):
            raise TypeError("Item must be of type IntDataType")
        self._data.append(item)

    def __len__(self) -> int:
        return len(self._data)

    def validate(self, data):
        for item in data:
            if not isinstance(item, IntDataType):
                raise TypeError("Data must be a list of IntDataType objects")


# Concrete implementation of DataAlgorithm
class IntAlgorithm(DataAlgorithm):
    """An algorithm specialized for processing IntDataType data."""

    @classmethod
    def input_data_type(cls):
        return IntDataType

    @classmethod
    def output_data_type(cls):
        return IntDataType


class IntCollectionMergeAlgorithm(DataAlgorithm):
    """An algorithm specialized for merging IntDataCollection data."""

    @classmethod
    def input_data_type(cls):
        return IntDataCollection

    @classmethod
    def output_data_type(cls):
        return IntDataType


# Concrete implementation of DataProbe
class IntProbe(DataProbe):
    """A probe specialized for processing IntDataType data."""

    @classmethod
    def input_data_type(cls):
        return IntDataType


class IntMultiplyAlgorithm(IntAlgorithm):
    """An algorithm specialized for multiplying IntDataType data."""

    def _operation(self, data, factor, *args, **kwargs):
        return IntDataType(data.data * factor)


class IntCollectionSumAlgorithm(IntCollectionMergeAlgorithm):
    """An algorithm specialized for summing IntDataCollection data."""

    def _operation(self, data, *args, **kwargs):
        return IntDataType(sum(item.data for item in data.data))


class IntCollectValueProbe(IntProbe):
    """A probe specialized for collecting the value of IntDataType data."""

    def _operation(self, data, *args, **kwargs):
        return data.data

    # Create a list of integers
    data = IntDataType(5)


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


def test_pipeline_execution_with_collection(int_data_collection, empty_context):
    """Test the execution of a pipeline with collection data."""
    # Define node configurations
    node_configurations = [
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
    # multiple data and 1 context, so it should be replicated
    # to match the number of data elements
    assert isinstance(context, ContextCollectionType)
    assert len(context) == 3


"""
def test_pipeline_slicing(int_data_collection, empty_context):
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
            "operation": IntCollectionMergeAlgorithm,
        },
    ]

    # Create a pipeline
    pipeline = Pipeline(node_configurations)
"""
