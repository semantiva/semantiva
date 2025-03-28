from typing import Any, Optional, Union
from collections import ChainMap
from typing import Any
from .context_types import ContextType, ContextCollectionType


class ContextObserver:
    """
    Centralized manager for context slicing, merging, and updates
    """

    def __init__(self):
        """
        Initialize the ContextObserver with an empty context.

        Attributes:
            context (dict): A dictionary to store contextual key-value pairs.
        """
        self.observer_context = ContextType

    @staticmethod
    def update_context(
        context: Union[ContextType, ContextCollectionType, ChainMap],
        key: str,
        value: Any,
        index: Optional[int] = None,
    ):
        """
        Updates a context value in either a single or collection context.

        - If `context` is a `ChainMap`, writes must be done on the **local context** (first mapping).
        - If `context` is `ContextCollectionType`, updates are applied globally or to a slice.

        Args:
            context (Union[ContextType, ContextCollectionType, ChainMap]): The context to update.
            key (str): The key to update.
            value (Any): The value to set.
            index (Optional[int]): The index of the slice to update (if context is a collection).

        Raises:
            ValueError: If attempting to update a collection without specifying an index.


        """
        if isinstance(context, ContextCollectionType):
            if index is None:
                context.set_value(key, value)
            else:
                context.set_item_value(index, key, value)
        elif isinstance(context, ChainMap):
            # ChainMap writes the first mapping (local context)
            context.maps[0][key] = value
        else:
            context.set_value(key, value)
