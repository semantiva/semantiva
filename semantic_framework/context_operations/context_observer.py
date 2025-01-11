class ContextObserver:
    """
    Class for managing and observing context updates within the semantic framework.

    This class f>acilitates the tracking and updating of contextual information
    that may influence the behavior of data operations and algorithms.
    """

    def __init__(self):
        """
        Initialize the ContextObserver with an empty context.

        Attributes:
            context (dict): A dictionary to store contextual key-value pairs.
        """
        self.context = {}

    def update_context(self, key: str, value: any):
        """
        Update the context with a new key-value pair or modify an existing one.

        Args:
            key (str): The key associated with the context value.
            value (any): The value to be stored in the context.
        """
        self.context[key] = value

    def get_context_value(self, key: str):
        """
        Retrieve the value associated with a given key in the context.

        Args:
            key (str): The key to look up in the context.

        Returns:
            any: The value associated with the key, or None if the key does not exist.
        """
        return self.context.get(key)

    def remove_context_key(self, key: str):
        """
        Remove a key-value pair from the context.

        Args:
            key (str): The key to be removed from the context.
        """
        if key in self.context:
            del self.context[key]

    def clear_context(self):
        """
        Clear all key-value pairs from the context.
        """
        self.context.clear()

    def __str__(self):
        """
        Provide a string representation of the current context.

        Returns:
            str: A string representation of the context dictionary.
        """
        return str(self.context)
