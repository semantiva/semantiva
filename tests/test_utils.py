# This file contains utility classes for testing the semantiva package.
from semantiva.data_types import BaseDataType, DataCollectionType
from semantiva.data_operations import DataAlgorithm, DataProbe


# Concrete implementation of BaseDataType for testing
class FloatDataType(BaseDataType[float]):
    """A data type for integers."""

    def validate(self, data: float) -> bool:
        if not isinstance(data, float):
            raise TypeError("Data must be a float")
        return True


# Concrete implementation of BaseDataType for testing in string
class IntDataType(BaseDataType[int]):
    """A data type for integers."""

    def validate(self, data: int) -> bool:
        if not isinstance(data, int):
            raise TypeError("Data must be an integer")
        return True


# Concrete implementation of DataCollectionType for testing
class FloatDataCollection(DataCollectionType[FloatDataType, list]):
    """A collection of IntDataType objects."""

    @classmethod
    def _initialize_empty(cls) -> list:
        return []

    def __iter__(self):
        return iter(self._data)

    def append(self, item: FloatDataType) -> None:
        if not isinstance(item, FloatDataType):
            raise TypeError("Item must be of type FloatDataType")
        self._data.append(item)

    def __len__(self) -> int:
        return len(self._data)

    def validate(self, data):
        for item in data:
            if not isinstance(item, FloatDataType):
                raise TypeError("Data must be a list of FloatDataType objects")


# Concrete implementation of DataAlgorithm
class FloatAlgorithm(DataAlgorithm):
    """An algorithm specialized for processing FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType


# Concrete implementation of DataAlgorithm
class IntAlgorithm(DataAlgorithm):
    """An algorithm specialized for processing IntDataType data."""

    @classmethod
    def input_data_type(cls):
        return IntDataType

    @classmethod
    def output_data_type(cls):
        return IntDataType


class FloatCollectionMergeAlgorithm(DataAlgorithm):
    """An algorithm specialized for merging FloatDataCollection data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataCollection

    @classmethod
    def output_data_type(cls):
        return FloatDataType


# Concrete implementation of DataProbe
class Float(DataProbe):
    """A probe specialized for processing FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataType


class FloatMultiplyAlgorithm(FloatAlgorithm):
    """An algorithm specialized for multiplying FloatDataType data."""

    def _operation(self, data, factor, *args, **kwargs):
        return FloatDataType(data.data * factor)


class IntMultiplyAlgorithm(IntAlgorithm):
    """An algorithm specialized for multiplying IntDataType data."""

    def _operation(self, data, factor, *args, **kwargs):
        return IntDataType(data.data * factor)


class FloatCollectionSumAlgorithm(FloatCollectionMergeAlgorithm):
    """An algorithm specialized for summing IntDataCollection data."""

    def _operation(self, data, *args, **kwargs):
        return FloatDataType(sum(item.data for item in data.data))


class FloatCollectValueProbe(Float):
    """A probe specialized for collecting the value of IntDataType data."""

    def _operation(self, data, *args, **kwargs):
        return data.data
