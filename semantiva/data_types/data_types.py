from typing import Type, TypeVar, Generic, Iterator, get_args, Optional
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

    def __init__(self, data: Optional[S] = None):
        """
        Initializes a DataSequence.

        Args:
            data (Optional[S]): The sequence data to initialize the object. Defaults to an empty sequence.
        """
        if data is None:
            data = (
                self._initialize_empty()
            )  # Use a class-specific method to create an empty instance
        super().__init__(data)

    @classmethod
    @abstractmethod
    def _initialize_empty(cls) -> S:
        """
        Defines how an empty DataSequence should be initialized.

        This method must be implemented by subclasses to return an empty instance
        of the appropriate sequence storage format.
        """
        pass

    @classmethod
    def sequence_base_type(cls) -> Type[E]:
        """
        Returns the base type of elements in the sequence.

        This method provides the expected data type of elements in the sequence
        based on the class definition.

        Returns:
            Type[E]: The expected type of elements in the sequence.
        """
        # Attempt to use get_args for fully parameterized generics
        args = get_args(cls)
        if args:
            return args[0]  # First argument should be `E`

        # Fallback: Inspect __orig_bases__ for non-parameterized generics
        for base in getattr(cls, "__orig_bases__", []):
            base_args = get_args(base)
            if base_args:
                return base_args[0]  # First argument should be `E`

        raise TypeError(f"{cls} is not a generic class with defined type arguments.")

    @abstractmethod
    def __iter__(self) -> Iterator[E]:
        """
        Returns an iterator over elements of type E.

        Returns:
            Iterator[E]: An iterator yielding elements of type E.
        """
        pass

    @abstractmethod
    def append(self, item: E) -> None:
        """
        Appends an element of type E to the data sequence.

        This method should be implemented by subclasses to define how elements
        are added to the sequence while ensuring consistency with the underlying storage format.

        Args:
            item (E): The element to append to the sequence.

        Raises:
            TypeError: If the item type does not match the expected element type.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Returns the number of elements in the sequence.

        Subclasses must implement this method to return the number of stored elements.

        Returns:
            int: The number of elements in the data sequence.
        """
        pass
