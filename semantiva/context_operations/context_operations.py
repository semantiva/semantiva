from typing import List, Optional
from abc import ABC, abstractmethod
from semantiva.context_operations.context_types import ContextType
from semantiva.logger import Logger


class ContextOperation(ABC):
    """
    Abstract base class for defining operations on a context.

    This class serves as a foundation for implementing specific operations
    that manipulate or utilize the context in various ways.
    """

    logger: Logger

    def __init__(self, logger: Optional[Logger] = None):
        if logger:
            # If a logger instance is provided, use it
            self.logger = logger
        else:
            # If no logger is provided, create a new Logger instance
            self.logger = Logger()
        self.logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def _operate_context(self, context: ContextType) -> ContextType:
        """
        Perform the core logic of the context operation.

        This method must be implemented by subclasses to define the specific
        operation to be performed on the given context.

        Args:
            context (ContextType): The context on which the operation is performed.

        Returns:
            ContextType: The modified (or unchanged) context after the operation.
        """

    def operate_context(self, context: ContextType) -> ContextType:
        """
        Execute the context operation.

        Calls the subclass-implemented `_operate_context` method to perform the
        operation on the provided context.

        Args:
            context (ContextType): The context to operate on.

        Returns:
            ContextType: The result of the context operation.
        """
        self.logger.debug(f"Executing {self.__class__.__name__}")
        return self._operate_context(context)

    @abstractmethod
    def get_required_keys(self) -> List[str]:
        """
        Retrieve a list of context keys required by this operation.

        Returns:
            List[str]: A list of context keys that the operation expects to be present
                       before execution.
        """

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """

    @abstractmethod
    def get_suppressed_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be suppressed or removed by this operation.

        Returns:
            List[str]: A list of context keys that the operation will remove or render
                       obsolete during its execution.
        """

    def __str__(self):
        return f"{self.__class__.__name__}"


class ContextPassthrough(ContextOperation):
    """
    A context operation that passes the context unchanged.

    This class is used as a default context operation for nodes when
    no specific context operation is provided.
    """

    def _operate_context(self, context: ContextType) -> ContextType:
        """
        Pass the context unchanged.

        Args:
            context (ContextType): The context to be passed through.

        Returns:
            ContextType: The unchanged context.
        """
        return context

    def get_required_keys(self) -> List[str]:
        """
        Since this operation does not require any specific keys,
        it returns an empty list.
        """
        return []

    def get_created_keys(self) -> List[str]:
        """
        Since this operation does not create any new keys,
        it returns an empty list.
        """
        return []

    def get_suppressed_keys(self) -> List[str]:
        """
        Since this operation does not suppress any keys,
        it returns an empty list.
        """
        return []


def rename_context_key(original_key: str, destination_key: str):
    """
    Factory function that creates a ContextOperation subclass to rename context keys.

    Args:
        original_key (str): The key to rename.
        destination_key (str): The new key name.

    Returns:
        Type[ContextOperation]: A dynamically generated class that renames context keys.
    """

    class RenameOperation(ContextOperation):
        """
        Dynamically generated context operation that renames a key in the context.
        """

        def _operate_context(self, context: ContextType) -> ContextType:
            """
            Rename a context key.

            Args:
                context (ContextType): The context to modify.

            Returns:
                ContextType: The updated context with the key renamed.
            """
            if original_key in context.keys():
                value = context.get_value(original_key)
                context.set_value(destination_key, value)
                context.delete_value(original_key)
                self.logger.info(
                    f"Renamed context key '{original_key}' -> '{destination_key}'"
                )
            else:
                self.logger.warning(f"Key '{original_key}' not found in context.")

            return context

        def get_required_keys(self) -> List[str]:
            """
            Since this operation requires the original key to be present,
            it returns a list containing the original key.
            """
            return [original_key]

        def get_created_keys(self) -> List[str]:
            """
            Since this operation creates a new key, it returns a list containing the new key.
            """
            return [destination_key]

        def get_suppressed_keys(self) -> List[str]:
            """
            Since this operation suppresses the original key, it returns a list containing the original key.
            """
            return [original_key]

    return RenameOperation  # Returns the class itself, not an instance


def delete_context_key(key: str):
    """
    Factory function that creates a ContextOperation subclass to delete a context key.

    Args:
        key (str): The key to delete.

    Returns:
        Type[ContextOperation]: A dynamically generated class that removes a key.
    """

    class DeleteOperation(ContextOperation):
        """
        A dynamically generated context operation that deletes a key from the context.
        """

        def _operate_context(self, context: ContextType) -> ContextType:
            """
            Remove a context key.

            Args:
                context (ContextType): The context to modify.

            Returns:
                ContextType: The updated context with the key removed.
            """
            if key in context.keys():
                context.delete_value(key)
                self.logger.info(f"Deleted context key '{key}'")
            else:
                self.logger.warning(f"Key '{key}' not found in context.")

            return context

        def get_required_keys(self) -> List[str]:
            """
            Since this operation does not require any specific keys,
            it returns an empty list.
            """
            return [key]

        def get_created_keys(self) -> List[str]:
            """
            Since this operation does not create any new keys,
            it returns an empty list.
            """
            return []

        def get_suppressed_keys(self) -> List[str]:
            """
            Since this operation suppresses the deleted key,
            it returns a list containing the key to be deleted.
            """
            return [key]

    return DeleteOperation  # Returns the class itself, not an instance
class FeatureFitWorkflow(ContextOperation):
    """ContextOperation that fits extracted features using a specified model."""

    def __init__(
        self,
        logger,
        fitting_model,
        independent_variable_parameter_name,
        dependent_variable_parameter_name,
        context_keyword,
    ):
        if logger:
            # If a logger instance is provided, use it
            self.logger = logger
        else:
            # If no logger is provided, create a new Logger instance
            self.logger = Logger()
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.fitting_model = fitting_model
        self.independent_variable_parameter_name = independent_variable_parameter_name
        self.dependent_variable_parameter_name = dependent_variable_parameter_name
        self.context_keyword = context_keyword

    def _operate_context(self, context):
        """Fit extracted features to the model using context data."""

        # Retrieve independent and dependent variables from context
        independent_variable = context.get(self.independent_variable_parameter_name)
        dependent_variable = context.get(self.dependent_variable_parameter_name)

        # Ensure required parameters exist
        if independent_variable is None or dependent_variable is None:
            missing_params = [
                p for p in self.get_required_keys() if context.get(p) is None
            ]
            raise ValueError(
                f"Missing required context parameters: {', '.join(missing_params)}"
            )

        # Fit the model using extracted features
        fit_results = self.fitting_model.fit(independent_variable, dependent_variable)

        # Store the results back in context under the dependent variable name
        context[self.context_keyword] = fit_results

        return context

    def get_required_keys(self) -> List[str]:
        """
        Since this operation does not require any specific keys,
        it returns an empty list.
        """
        return [
            self.independent_variable_parameter_name,
            self.dependent_variable_parameter_name,
        ]

    def get_created_keys(self) -> List[str]:
        """
        Since this operation does not create any new keys,
        it returns an empty list.
        """
        return [self.context_keyword]

    def get_suppressed_keys(self) -> List[str]:
        """
        Since this operation does not suppress any keys,
        it returns an empty list.
        """
        return []
