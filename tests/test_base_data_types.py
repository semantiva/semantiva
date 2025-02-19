import pytest
from semantiva.data_types.data_types import BaseDataType, DataCollectionType
from .test_utils import IntDataType, IntDataCollection


# Tests for BaseDataType
def test_base_data_type():
    """Test the BaseDataType class."""
    int_data = IntDataType(10)
    assert int_data.data == 10

    with pytest.raises(TypeError):
        IntDataType("not an int")

    int_data.data = 20
    assert int_data.data == 20


# Tests for DataCollectionType
def test_data_collection_type():
    """Test the DataCollectionType class."""
    collection = IntDataCollection()
    assert len(collection) == 0

    int_data1 = IntDataType(10)
    int_data2 = IntDataType(20)

    collection.append(int_data1)
    collection.append(int_data2)

    assert len(collection) == 2
    assert list(collection) == [int_data1, int_data2]

    with pytest.raises(TypeError):
        collection.append("not an IntDataType")

    collection_from_list = IntDataCollection.from_list([int_data1, int_data2])
    assert len(collection_from_list) == 2
    assert list(collection_from_list) == [int_data1, int_data2]


def test_data_collection_iter():
    collection = IntDataCollection()
    int_data1 = IntDataType(10)
    int_data2 = IntDataType(20)
    collection.append(int_data1)
    collection.append(int_data2)

    items = [item for item in collection]
    assert items == [int_data1, int_data2]


def test_data_collection_len():
    collection = IntDataCollection()
    assert len(collection) == 0

    int_data1 = IntDataType(10)
    int_data2 = IntDataType(20)
    collection.append(int_data1)
    collection.append(int_data2)

    assert len(collection) == 2


if __name__ == "__main__":
    pytest.main()
