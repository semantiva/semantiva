from typing import Any
from .context_types import ContextType


class ContextObserver:
    """
    Class for managing and observing context updates within the semantic framework.

    This class facilitates the tracking and updating of contextual information
    that may influence the behavior of data operations and algorithms.
    """

    def __init__(self):
        """
        Initialize the ContextObserver with an empty context.

        Attributes:
            context (dict): A dictionary to store contextual key-value pairs.
        """
        self.observer_context = ContextType

    def update_context(self, key: str, value: Any):
        """
        Update the context with a new key-value pair or modify an existing one.

        Args:
            key (str): The key associated with the context value.
            value (any): The value to be stored in the context.
        """
        self.observer_context.set_value(key, value)

    def __str__(self):
        """
        Provide a string representation of the current context.

        Returns:
            str: A string representation of the context dictionary.
        """
        return str(self.observer_context)
