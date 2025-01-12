from typing import Any
from abc import ABC, abstractmethod


class BaseDataType(ABC):
    """
    Abstract base class for all data types in the semantic framework.

    This class provides a foundation for creating and managing various data types,
    ensuring consistency and extensibility across the framework.

    Attributes:
        _data (Any): The underlying data encapsulated by the data type.
    """

    _data: Any

    def __init__(self, data: Any):
        """
        Initialize the BaseDataType with the provided data.

        Args:
            data (Any): The data to be encapsulated by this data type.
        """
        self.validate(data)
        self._data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        Abstract method to validate the encapsulated data.

        This method must be implemented by subclasses to define specific
        validation rules for the data type.

        Returns:
            bool: True if the data is valid, False otherwise.
        """
        pass


class DataSequence(BaseDataType):
    """
    Abstract base class for sequence-based data types.

    This class extends BaseDataType to handle data that is inherently sequential
    and provides a foundation for sequence-specific operations.
    """

    @abstractmethod
    def sequence_base_type(self) -> type:
        """
        Abstract method to define the base type of elements in the sequence.

        This method must be implemented by subclasses to specify the expected
        data type of elements in the sequence.

        Returns:
            type: The expected type of elements in the sequence.
        """
        pass
