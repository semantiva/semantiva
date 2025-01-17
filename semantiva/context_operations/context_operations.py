from typing import List
from abc import ABC, abstractmethod
from .context_types import ContextType


class ContextOperation(ABC):
    """
    Abstract base class for defining operations on a context.

    This class serves as a foundation for implementing specific operations
    that manipulate or utilize the context in various ways.
    """

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
