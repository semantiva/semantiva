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
            data (T): The data to be encapsulated by this data type.
        """
        self.validate(data)
        self._data = data

    @property
    def data(self) -> T:
        return self._data

    @data.setter
    def data(self, data: T):
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
S = TypeVar("S")  # The preferred storage format for the collection


class DataCollectionType(BaseDataType[S], Generic[E, S]):
    """
    Abstract base class for collection-based data types.

    This class extends BaseDataType to handle data that comprises multiple
    elements and provides a foundation for collection-specific operations.
    """

    def __init__(self, data: Optional[S] = None):
        """
        Initializes a DataCollectionType.

        Args:
            data (Optional[S]): The initial collection data to initialize the object.
                Defaults to an empty collection via _initialize_empty().
        """
        if data is None:
            data = self._initialize_empty()
        super().__init__(data)

    @classmethod
    @abstractmethod
    def _initialize_empty(cls) -> S:
        """
        Defines how an empty DataCollectionType should be initialized.

        This method must be implemented by subclasses to return an empty
        instance of the appropriate collection storage format.
        """
        pass

    @classmethod
    def collection_base_type(cls) -> Type[E]:
        """
        Returns the base type of elements in the collection.

        This method provides the expected data type for elements in the collection
        based on the class definition.

        Returns:
            Type[E]: The expected type of elements in the collection.
        """
        # Attempt get_args(...) first to retrieve type arguments for classes that are
        # fully parameterized at runtime. This covers most modern Python generics.        args = get_args(cls)
        args = get_args(cls)
        if args:
            return args[0]  # First argument should be `E`

        # If get_args(...) yields no results, fallback to scanning __orig_bases__.
        # In certain mypy or older Python generics scenarios, type parameters are
        # registered there rather than in get_args(...).
        for base in getattr(cls, "__orig_bases__", []):
            base_args = get_args(base)
            if base_args:
                return base_args[0]  # First argument should be `E`

        raise TypeError(f"{cls} is not a generic class with defined type arguments.")

    @abstractmethod
    def __iter__(self) -> Iterator[E]:
        """
        Returns an iterator over elements of type E within the collection.

        Returns:
            Iterator[E]: An iterator yielding elements of type E.
        """
        pass

    @abstractmethod
    def append(self, item: E) -> None:
        """
        Appends an element of type E to the data collection.

        Subclasses should implement how elements are added to the underlying
        storage format while ensuring consistency.

        Args:
            item (E): The element to append to the collection.

        Raises:
            TypeError: If the item type does not match the expected element type.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Returns the number of elements in the data collection.

        Subclasses must implement this method to return the number of stored elements.

        Returns:
            int: The number of elements in the collection.
        """
        pass

    @classmethod
    def from_list(cls, items: list[E]) -> "DataCollectionType[E, S]":
        """
        Creates a DataCollectionType object from a list of BaseDataType objects.

        Args:
            items (list[E]): A list of BaseDataType objects to initialize the collection.

        Returns:
            DataCollectionType[E, S]: A new instance of DataCollectionType with the items.
        """
        instance = cls(cls._initialize_empty())
        for item in items:
            instance.append(item)
        return instance


class NoDataType(BaseDataType[None]):
    """
    A data type representing the absence of data in Semantiva.
    """

    def validate(self, data: None) -> bool:
        return data is None

    def __str__(self) -> str:
        return "NoDataType"

    def __init__(self, data: None = None, *args, **kwargs):
        """
        Initializes a NoDataType instance
        """
        super().__init__(data, *args, **kwargs)
