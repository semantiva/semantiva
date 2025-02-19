# This file contains utility classes for testing the semantiva package.
from semantiva.data_types import BaseDataType, DataCollectionType
from semantiva.data_operations import DataAlgorithm, DataProbe


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
