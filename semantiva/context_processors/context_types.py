from typing import Any, List, Optional, Iterator, Union, Dict, Tuple
from ..logger import Logger


class ContextType:
    """
    Represents a generic context within the framework.

    This class serves as a container for storing and managing context-specific
    information, facilitating access and updates to context data.

    Attributes:
        _context_container (dict): A dictionary that stores key-value pairs representing
                                   the context data.
    """

    def __init__(
        self, context_dict: Optional[Dict] = None, logger: Optional[Logger] = None
    ):
        """
        Initialize a ContextType with an optional context_dict.

        Args:
            context_dict (Optional[Dict], optional): A dictionary of initial context data.
                                                    Defaults to None, resulting in an empty context.
        """
        self._context_container = {} if context_dict is None else context_dict
        if logger is not None:
            self.logger = logger
        else:
            self.logger = Logger()

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContextType):
            return False
        return self._context_container == other._context_container


class ContextCollectionType(ContextType):
    """
    A specialized context type that stores and manages multiple `ContextType` instances.

    This class extends `ContextType` but internally keeps a list of separate contexts.
    Each item in the collection is a `ContextType`, enabling parallel iteration with
    DataC subclasses that contain multiple data items.
    """

    def __init__(
        self,
        collection_context: Optional[Union[ContextType, Dict]] = None,
        context_list: Optional[List[ContextType]] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ContextCollectionType instance that manages multiple ContextType items.

        In this specialized context, two separate containers are maintained:
        - The collection context (inherited from ContextType) holds global or shared key-value pairs.
        - The individual context list (_context_list) holds multiple ContextType instances, allowing
            for parallel storage and iteration of separate contexts.

        The collection_context parameter can be provided in two forms:
        • As a dictionary, which will be used directly.
        • As a ContextType, in which case its internal _context_container is extracted.
        If collection_context is None, an empty dictionary will be used.

        Args:
            collection_context (Optional[Union[ContextType, Dict]]): Global context data, either as a
                ContextType instance or a dictionary. Defaults to None.
            context_list (Optional[List[ContextType]]): A list of individual ContextType instances.
                If None, an empty list is initialized.
            logger (Optional[Logger]): A Logger instance used for logging within the context.
                If None, a default Logger is instantiated.
        """
        # Determine the base context container:
        # - If no collection_context is provided, initialize with an empty dict.
        # - If collection_context is a dict, use it as-is.
        # - If it's a ContextType, extract its _context_container.
        collection_context_ = (
            {}
            if collection_context is None
            else (
                collection_context
                if isinstance(collection_context, dict)
                else collection_context._context_container
            )
        )
        # Initialize the base ContextType with the determined context container and logger.
        super().__init__(context_dict=collection_context_, logger=logger)
        # Initialize the list to hold individual ContextType instances.
        self._context_list: List[ContextType] = (
            context_list if context_list is not None else []
        )

    def __iter__(self) -> Iterator[ContextType]:
        """
        Return an iterator over the stored `ContextType` instances.

        Yields:
            ContextType: Each context in the collection.
        """
        return iter(self._context_list)

    def __len__(self) -> int:
        """
        Return the number of context elements in this collection.

        Returns:
            int: The length of the internal list of `ContextType`s.
        """
        return len(self._context_list)

    def append(self, item: ContextType) -> None:
        """
        Append a `ContextType` object to the end of this collection.

        Args:
            item (ContextType): The context to be appended.

        Raises:
            TypeError: If the provided item is not a `ContextType` instance.
        """
        if not isinstance(item, ContextType):
            raise TypeError(f"Expected ContextType, got {type(item)}")
        self._context_list.append(item)

    def __getitem__(self, index: int) -> ContextType:
        return self.get_item(index)

    ###################### Overriden ContextType methods tailored for collections  ######################

    def __str__(self) -> str:
        """
        Return a string representation of the collection, showing its length,
        global context, and individual contexts.

        Returns:
            str: A descriptive string of this collection object.
        """
        global_str = f"global_context={self._context_container}"
        individual_str = (
            f"individual_contexts={[str(ctx) for ctx in self._context_list]}"
        )
        return f"{self.__class__.__name__}(length={len(self._context_list)}, {global_str}, {individual_str})"

    def get_item(self, index: int) -> ContextType:
        """
        Retrieve and combine an individual ContextType instance with the global collection context.

        This method fetches the ContextType at the specified index from the internal
        context list (_context_list) and merges its key-value pairs with those from the
        global collection context (_context_container).

        In the event that the same key exists in both contexts an exception is raised
        because this case indicates a fragile data structure design.

        Args:
            index (int): The index of the desired individual context.

        Returns:
            ContextType: A new ContextType instance representing the merged context.
                Keys from the global context override those in the individual context.
        """
        item_context = self._context_list[index]

        # Check for overlapping keys between the individual context and the global collection.
        # If an overlap is found, log a warning and proceed with the global value.
        for key in item_context.keys():
            if key in self._context_container:
                raise ValueError(
                    f"Key '{key}' is present in both the global collection and the individual context. "
                    "This fragile data structure design prevents proper merging.\n="
                    "Consider renaming the key or use a ContextProcessor to improve the data structure."
                )

        # Merge dictionaries: keys from the global collection (_context_container)
        # take precedence over those in the individual context.
        combined_context = ContextType(
            {**self._context_container, **item_context._context_container}
        )
        return combined_context

    def get_value(self, key: str) -> Any:
        """
        Retrieve a value from the context collection for the specified key.

        This method searches for the specified key in both the global context
        (_context_container) and the individual contexts (_context_list). It applies
        the following rules:
        - If the key is present only in the global context, return the corresponding value.
        - If the key is present only in individual contexts, return a list of values,
          one for each context (using None when the key is missing in a particular context).
          If all individual contexts return None, then return None.
        - If the key is present in both the global context and any individual context, raise a
          ValueError because this overlap indicates a fragile data structure design.

        Args:
            key (str): The key for which to retrieve the value.

        Returns:
            Any: The value associated with the key. This may be a single value (from the global context),
                a list of values (from individual contexts), or None if the key is not found.
        """
        in_global = key in self._context_container
        # Always collect a list of values from individual contexts.
        individual_values = [context.get_value(key) for context in self._context_list]

        # If the key exists in both global and any individual context, raise an exception.
        if in_global and any(value is not None for value in individual_values):
            raise ValueError(
                f"Key '{key}' is present in both the global collection and individual contexts. "
                "This fragile data structure design prevents proper merging. "
                "Consider renaming the key or using a ContextProcessor to improve the data structure."
            )

        # Return the value from the global context if it exists.
        if in_global:
            return self._context_container.get(key)

        # If any individual context provided a non-None value, return the list.
        if any(value is not None for value in individual_values):
            return individual_values

        # If the key is not found anywhere, return None.
        return None

    def set_value(self, key: str, value: Any):
        """
        Set or update a value in the context collection.

        This method applies the following rules:
        - If the key is present in the collection (global) context, update its value and
            remove the key from any individual contexts to avoid conflicts.
        - If the key is present only in one or more individual contexts, update the value
            in all individual contexts.
        - If the key is not found in either the global or individual contexts, add it to the
            global collection context.

        Args:
            key (str): The key associated with the value to update or set.
            value (Any): The new value to assign to the key.
        """
        # If key exists in the global collection, update it.
        if key in self._context_container:
            self._context_container[key] = value

        # If key exists in any individual context, update all of them.
        elif key in self.keys():
            for context in self._context_list:
                context.set_value(key, value)
        # Otherwise, add the key to the global context.
        else:
            self._context_container[key] = value

    def set_item_value(self, index: int, key: str, value: Any):
        """
        Set or update the value of a single item.

        - If the key is present in the global context, raise an exception.
        - If the key is present in the individual context, update it.
          If not present, simply set it.

        Args:
            index (int): The index of the individual context to update.
            key (str): The key whose value is to be set.
            value (Any): The new value to assign.

        Raises:
            ValueError: If the key exists in the global collection context.
        """
        if key in self._context_container:
            raise ValueError(
                f"Key '{key}' is present in the global collection and cannot be set on an individual item."
            )

        # Retrieve the target individual context.
        target_context = self._context_list[index]
        # Update or set the key-value pair in that context.
        target_context.set_value(key, value)

    def delete_value(self, key: str):
        """
        Remove a key-value pair from the context collection.

        This method removes the specified key from both the collection (global) context
        and any individual contexts held within the collection. It applies the following rules:
        - If the key is present in the global collection context, remove it.
        - If the key is present in any individual contexts, remove it from each of them.
        - If the key is not found in either the global context or any individual contexts,
            raise a KeyError.

        Args:
            key (str): The key to be removed from the context.

        Raises:
            KeyError: If the key is not found in the collection context or any individual contexts.
        """
        found = False

        # Remove key from the global context if it exists.
        if key in self._context_container:
            del self._context_container[key]
            found = True

        # Remove key from each individual context if present.
        for context in self._context_list:
            if key in context.keys():
                context.delete_value(key)
                found = True

        # If the key wasn't found anywhere, raise an error.
        if not found:
            raise KeyError(f"Key '{key}' not found in context.")

    def clear(self):
        """
        Clear all key-value pairs from the context collection.

        This method resets the global context (_context_container) to an empty dictionary and
        clears all key-value pairs from each individual ContextType stored in the
        internal context list (_context_list). This ensures that the entire ContextCollectionType
        is reset to an empty state.
        """
        self._context_container.clear()
        for context in self._context_list:
            context.clear()

    def keys(self) -> List[str]:
        """
        Retrieve all keys in the context collection.

        This method collects keys from both the global context (_context_container)
        and each individual context in (_context_list). If a key is found to be present
        in both the global context and any individual context, a ValueError is raised,
        as this indicates an ambiguous or fragile data structure design.

        Returns:
            list: A combined list of all keys present in either the global or individual contexts.
        """
        # Get keys from the global context.
        global_keys = set(self._context_container.keys())

        # Get all keys from individual contexts.
        individual_keys = set()
        for context in self._context_list:
            individual_keys.update(context.keys())

        # If a key appears in both, raise an exception.
        conflict_keys = global_keys.intersection(individual_keys)
        if conflict_keys:
            raise ValueError(
                f"Conflicting key(s) found in both global and individual contexts: {', '.join(conflict_keys)}. "
                "This fragile data structure design prevents proper merging. "
                "Consider renaming the key or using a ContextProcessor to improve the data structure."
            )

        # Return the union of keys.
        combined_keys = global_keys.union(individual_keys)
        return list(combined_keys)

    def values(self) -> List[Any]:
        """
        Retrieve all values in the context collection.

        This method iterates over all keys obtained from the collection (both global and individual)
        using self.keys(). For each key, it retrieves the associated value by calling self.get_value(key).

        The retrieval rules are as follows:
        - If the key is present only in the global context, its value is returned.
        - If the key is present only in one or more individual contexts, a list of values from
            all those individual contexts is returned.
        - If a key exists in both contexts, a ValueError is raised (as enforced by self.get_value).

        Returns:
            List[Any]: A list of values corresponding to each key in the context collection.
        """
        return [self.get_value(key) for key in self.keys()]

    def items(self) -> List[Tuple[str, Any]]:
        """
        Retrieve all key-value pairs in the context collection.

        This method uses self.keys() to retrieve a combined list of keys from the global
        context (_context_container) and all individual contexts (_context_list). For each key,
        it then obtains the associated value via self.get_value(key), which applies the rules for
        merging or conflict handling between the global and individual contexts.

        Returns:
            List[Tuple[str, Any]]: A list of (key, value) tuples for all keys present in the context.
                                The values may be a single value or a list of values, depending on
                                where the key is defined.
        """
        return [(key, self.get_value(key)) for key in self.keys()]
