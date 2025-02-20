import pytest
from .test_utils import FloatDataType, FloatDataCollection


# Tests for BaseDataType
def test_base_data_type():
    """Test the BaseDataType class."""
    float_data = FloatDataType(10.0)
    assert float_data.data == 10.0

    with pytest.raises(TypeError):
        FloatDataType("not an int")

    float_data.data = 20.0
    assert float_data.data == 20.0


# Tests for DataCollectionType
def test_data_collection_type():
    """Test the DataCollectionType class."""
    collection = FloatDataCollection()
    assert len(collection) == 0

    float_data1 = FloatDataType(10.0)
    float_data2 = FloatDataType(20.0)

    collection.append(float_data1)
    collection.append(float_data2)

    assert len(collection) == 2
    assert list(collection) == [float_data1, float_data2]

    with pytest.raises(TypeError):
        collection.append("not an IntDataType")

    collection_from_list = FloatDataCollection.from_list([float_data1, float_data2])
    assert len(collection_from_list) == 2
    assert list(collection_from_list) == [float_data1, float_data2]


def test_data_collection_iter():
    """Test the __iter__ method of DataCollection"""
    collection = FloatDataCollection()
    float_data1 = FloatDataType(10.0)
    float_data2 = FloatDataType(20.0)
    collection.append(float_data1)
    collection.append(float_data2)

    items = [item for item in collection]
    assert items == [float_data1, float_data2]


def test_data_collection_len():
    """Test the __len__ method of DataCollection"""
    collection = FloatDataCollection()
    assert len(collection) == 0

    float_data1 = FloatDataType(10.0)
    float_data2 = FloatDataType(20.0)
    collection.append(float_data1)
    collection.append(float_data2)

    assert len(collection) == 2


if __name__ == "__main__":
    pytest.main()
