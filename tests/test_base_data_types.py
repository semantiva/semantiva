import pytest
from semantiva.data_types.data_types import BaseDataType, DataCollectionType


# Concrete implementation of BaseDataType for testing
class IntDataType(BaseDataType[int]):
    def validate(self, data: int) -> bool:
        if not isinstance(data, int):
            raise TypeError("Data must be an integer")
        return True


# Concrete implementation of DataCollectionType for testing
class IntDataCollection(DataCollectionType[IntDataType, list]):
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


# Tests for BaseDataType
def test_base_data_type():
    int_data = IntDataType(10)
    assert int_data.data == 10

    with pytest.raises(TypeError):
        IntDataType("not an int")

    int_data.data = 20
    assert int_data.data == 20


# Tests for DataCollectionType
def test_data_collection_type():
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
