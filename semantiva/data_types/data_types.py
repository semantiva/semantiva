from typing import Type, TypeVar, Generic, Iterator
from abc import ABC, abstractmethod


T = TypeVar("T")


class BaseDataType(ABC, Generic[T]):
    """
    Abstract generic base class for all data types in the semantic framework.

    This class provides a foundation for creating and managing various data types,
    ensuring consistency and extensibility across the framework.

    Attributes:
        _data (T): The underlying data encapsulated by the data type.
    """

    _data: T

    def __init__(self, data: T):
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
    def validate(self, data: T) -> bool:
        """
        Abstract method to validate the encapsulated data.

        This method must be implemented by subclasses to define specific
        validation rules for the data type.

        Returns:
            bool: True if the data is valid, False otherwise.
        """


E = TypeVar("E", bound=BaseDataType)
S = TypeVar("S")  # The preferred storage format for the sequence


class DataSequence(BaseDataType[S], Generic[E, S]):
    """
    Abstract base class for sequence-based data types.

    This class extends BaseDataType to handle data that is inherently sequential
    and provides a foundation for sequence-specific operations.
    """

    def __init__(self, data: S):
        super().__init__(data)

    @classmethod
    def sequence_base_type(cls) -> Type[E]:
        """
        Returns the base type of elements in the sequence.

        This method provides the expected data type of elements in the sequence
        based on the class definition.

        Returns:
            Type[E]: The expected type of elements in the sequence.
        """
        return cls.__orig_bases__[0].__args__[0]  # Extracts the bound type dynamically

    @abstractmethod
    def __iter__(self) -> Iterator[E]:
        """
        Returns an iterator over elements of type E.

        Returns:
            Iterator[E]: An iterator yielding elements of type E.
        """
        pass
