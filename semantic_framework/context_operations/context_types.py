from typing import Any, List, Tuple, Dict, Optional


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
        Initialize an empty context.

        The context is represented by an internal dictionary that stores
        all key-value pairs.
        """
        self._context_container = {} if context_dict is None else context_dict

    def get_value(self, key: str) -> Any:
        """
        Retrieve a value from the context using the specified key.

        Args:
            key (str): The key associated with the desired value.

        Returns:
            Any: The value corresponding to the key, or None if the key
                 does not exist.
        """
        return self._context_container.get(key)

    def set_value(self, key: str, value: Any):
        """
        Set or update a value in the context.

        Args:
            key (str): The key associated with the value to be stored.
            value (Any): The value to store in the context.

        Returns:
            None
        """
        self._context_container[key] = value

    def delete_value(self, key: str):
        """
        Remove a key-value pair from the context.

        Args:
            key (str): The key to be removed from the context.

        Raises:
            KeyError: If the key does not exist in the context.

        Returns:
            None
        """
        if key not in self._context_container:
            raise KeyError(f"Key '{key}' not found in context.")
        del self._context_container[key]

    def clear(self):
        """
        Clear all key-value pairs in the context.

        This method resets the context to an empty state.

        Returns:
            None
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
            list: A list of tuples, where each tuple contains a key and
                  its corresponding value.
        """
        return list(self._context_container.items())

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(context={self._context_container})"
