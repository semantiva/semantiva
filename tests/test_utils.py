# This file contains utility classes for testing the semantiva package.
from semantiva.data_types import BaseDataType, DataCollectionType
from semantiva.data_processors import DataOperation, DataProbe
from semantiva.data_io import DataSource, DataSink


# Concrete implementation of BaseDataType for testing
class FloatDataType(BaseDataType[float]):
    """A data type for integers."""

    def validate(self, data: float) -> bool:
        if not isinstance(data, float):
            raise TypeError("Data must be a float")
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


# Concrete implementation of DataOperation
class FloatOperation(DataOperation):
    """An operation specialized for processing FloatDataType data."""

    @staticmethod
    def input_data_type():
        return FloatDataType

    @staticmethod
    def output_data_type():
        return FloatDataType


class FloatCollectionMergeOperation(DataOperation):
    """An operation specialized for merging FloatDataCollection data."""

    @staticmethod
    def input_data_type():
        return FloatDataCollection

    @staticmethod
    def output_data_type():
        return FloatDataType


# Concrete implementation of DataProbe
class Float(DataProbe):
    """A probe specialized for processing FloatDataType data."""

    @staticmethod
    def input_data_type():
        return FloatDataType


class FloatMultiplyOperation(FloatOperation):
    """An operation specialized for multiplying FloatDataType data."""

    def _process_logic(self, data, factor, *args, **kwargs):
        return FloatDataType(data.data * factor)


class FloatCollectionSumOperation(FloatCollectionMergeOperation):
    """An operation specialized for summing IntDataCollection data."""

    def _process_logic(self, data, *args, **kwargs):
        return FloatDataType(sum(item.data for item in data.data))


class FloatCollectValueProbe(Float):
    """A probe specialized for collecting the value of IntDataType data."""

    def _process_logic(self, data, *args, **kwargs):
        return data.data


class FloatMockDataSource(DataSource):
    """Concrete implementation of DataSource providing FloatDataType data."""

    def _get_data(self, *args, **kwargs) -> FloatDataType:
        return FloatDataType(123.0)

    @staticmethod
    def output_data_type():
        return FloatDataType


class FloatMockDataSink(DataSink):
    """Concrete implementation of Datasink for FloatDataType data."""

    def _send_data(self, data: BaseDataType, path: str, *args, **kwargs):
        return

    @staticmethod
    def input_data_type():
        return FloatDataType
