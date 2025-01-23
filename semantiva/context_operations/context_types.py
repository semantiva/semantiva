from typing import Any, List, Optional, Iterator, Union, Dict, Tuple


class ContextType:
    """
    Represents a generic context within the framework.

    This class serves as a container for storing and managing context-specific
    information, facilitating access and updates to context data.

    Attributes:
        _context_container (dict): A dictionary that stores key-value pairs representing
                                   the context data.
    """

    def __init__(self, context_dict: Optional[Dict] = None):
        """
        Initialize a ContextType with an optional context_dict.

        Args:
            context_dict (Optional[Dict], optional): A dictionary of initial context data.
                                                    Defaults to None, resulting in an empty context.
        """
        self._context_container = {} if context_dict is None else context_dict

    def get_value(self, key: str) -> Any:
        """
        Retrieve a value from the context using the specified key.

        Args:
            key (str): The key associated with the desired value.

        Returns:
            Any: The value corresponding to the key, or None if the key does not exist.
        """
        return self._context_container.get(key)

    def set_value(self, key: str, value: Any):
        """
        Set or update a value in the context.

        Args:
            key (str): The key associated with the value to be stored.
            value (Any): The value to store in the context.
        """
        self._context_container[key] = value

    def delete_value(self, key: str):
        """
        Remove a key-value pair from the context.

        Args:
            key (str): The key to be removed from the context.

        Raises:
            KeyError: If the key does not exist in the context.
        """
        if key not in self._context_container:
            raise KeyError(f"Key '{key}' not found in context.")
        del self._context_container[key]

    def clear(self):
        """
        Clear all key-value pairs in the context.

        This method resets the context to an empty state.
        """
        self._context_container.clear()

    def keys(self) -> List[str]:
        """
        Retrieve all keys in the context.

        Returns:
            list: A list of all keys currently stored in the context.
        """
        return list(self._context_container.keys())

    def values(self) -> List[Any]:
        """
        Retrieve all values in the context.

        Returns:
            list: A list of all values currently stored in the context.
        """
        return list(self._context_container.values())

    def items(self) -> List[Tuple[str, Any]]:
        """
        Retrieve all key-value pairs in the context.

        Returns:
            list: A list of (key, value) tuples for the stored context data.
        """
        return list(self._context_container.items())

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(context={self._context_container})"


class ContextSequenceType(ContextType):
    """
    A specialized context type that stores and manages multiple `ContextType` instances.

    This class extends `ContextType` but internally keeps a list of separate contexts.
    Each item in the sequence is a `ContextType`, enabling parallel iteration with
    DataSequence subclasses that contain multiple data items.
    """

    def __init__(self, context_list: Optional[List[ContextType]] = None):
        """
        Initialize a `ContextSequenceType` with an optional list of `ContextType` instances.

        Args:
            context_list (Optional[List[ContextType]]): A list of `ContextType` objects
                                                       to initialize the sequence. If None,
                                                       an empty list is used.
        """
        # We won't use _context_container from the base for storing items; we store them in a list.
        super().__init__()
        self._context_list: List[ContextType] = (
            context_list if context_list is not None else []
        )

    def __iter__(self) -> Iterator[ContextType]:
        """
        Return an iterator over the stored `ContextType` instances.

        Yields:
            ContextType: Each context in the sequence.
        """
        return iter(self._context_list)

    def __len__(self) -> int:
        """
        Return the number of context elements in this sequence.

        Returns:
            int: The length of the internal list of `ContextType`s.
        """
        return len(self._context_list)

    def append(self, item: ContextType) -> None:
        """
        Append a `ContextType` object to the end of this sequence.

        Args:
            item (ContextType): The context to be appended.

        Raises:
            TypeError: If the provided item is not a `ContextType` instance.
        """
        if not isinstance(item, ContextType):
            raise TypeError(f"Expected ContextType, got {type(item)}")
        self._context_list.append(item)

    def __getitem__(self, index: int) -> ContextType:
        """
        Retrieve a specific `ContextType` from the sequence by index.

        Args:
            index (int): The index of the desired context.

        Returns:
            ContextType: The context at the specified index.
        """
        return self._context_list[index]

    def __str__(self) -> str:
        """
        Return a string representation of the sequence, showing its length.

        Returns:
            str: A descriptive string of this sequence object.
        """
        return f"{self.__class__.__name__}(length={len(self._context_list)})"
