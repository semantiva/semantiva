# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import abstractmethod
from typing import Dict, Any, Type, TypeVar, Generic, Iterator, get_args, Optional
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.logger import Logger

T = TypeVar("T")


class BaseDataType(_SemantivaComponent, Generic[T]):
    """
    Abstract generic base class for all data types in the semantic framework.

    This class provides a foundation for creating and managing various data types,
    ensuring consistency and extensibility across the framework.

    Attributes:
        _data (T): The underlying data encapsulated by the data type.
    """

    _data: T

    def __init__(self, data: T, logger: Optional[Logger] = None):
        """
        Initialize the BaseDataType with the provided data.

        Args:
            data (T): The data to be encapsulated by this data type.
            logger (Optional[Logger]): Optional logger instance.
        """
        super().__init__(logger)
        self.validate(data)
        self._data = data

    @property
    def data(self) -> T:
        """
        Get the encapsulated data.

        Returns:
            T: The underlying data stored in this data type instance.
        """
        return self._data

    @data.setter
    def data(self, data: T):
        """Set the encapsulated data after validation.

        Args:
            data (T): The new data to store in this data type.
        """
        self._data = data

    def validate(self, data: T) -> bool:
        """
        Abstract method to validate the encapsulated data.

        This method must be implemented by subclasses to define specific
        validation rules for the data type.

        Returns:
            bool: True if the data is valid, False otherwise.
        """
        return True

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:

        # Define the metadata for the BaseDataType
        component_metadata = {
            "component_type": "BaseDataType",
        }

        return component_metadata

    def __str__(self):
        return f"{self.__class__.__name__}({self.data})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"


E = TypeVar("E", bound=BaseDataType)
S = TypeVar("S")  # The preferred storage format for the collection


class DataCollectionType(BaseDataType[S], Generic[E, S]):
    """Abstract base class for data collections, handling multiple elements of the same BaseDataType."""

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
    def _define_metadata(cls) -> Dict[str, Any]:

        # Define the metadata for the DataCollectionType
        component_metadata = {
            "component_type": "DataCollectionType",
        }
        # try to resolve the element type, but fail gracefully
        try:
            element_cls = cls.collection_base_type()
            if hasattr(element_cls, "get_metadata"):
                elem_meta = element_cls.get_metadata().get(
                    "component_type", element_cls.__name__
                )
                component_metadata["collection_element_type"] = (
                    f"{element_cls.__name__}<{elem_meta}>"
                )
            else:
                # element_cls is not a _SemantivaComponent subclass (e.g. still a TypeVar)
                component_metadata["collection_element_type"] = BaseDataType.__name__
        except Exception:
            # no binding available at this abstract level
            pass

        return component_metadata

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
        # Attempt to retrieve type arguments for classes that are fully
        # parameterized at runtime. This covers most modern Python generics.
        args = get_args(cls)
        if args:
            return args[0]  # First argument should be `E`

        # If ``get_args`` yields no results, fall back to scanning
        # ``__orig_bases__``. In certain mypy or older Python generics
        # scenarios, type parameters are registered there rather than in
        # ``get_args``.
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
        """Validate that no data is provided.

        Args:
            data (None): Should always be ``None``.

        Returns:
            bool: ``True`` if ``data`` is ``None``, ``False`` otherwise.
        """
        return data is None

    def __str__(self) -> str:
        return "NoDataType"

    def __init__(self, data: None = None, *args, **kwargs):
        """
        Initializes a NoDataType instance
        """
        super().__init__(data, *args, **kwargs)
