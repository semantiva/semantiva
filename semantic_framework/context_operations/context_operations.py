from abc import ABC, abstractmethod
from .context_types import ContextType

class ContextOperation(ABC):
    """
    Abstract base class for defining operations on a context.

    This class serves as a foundation for implementing specific operations
    that manipulate or utilize the context in various ways.
    """

    @abstractmethod
    def _operate_context(self, context: ContextType):
        """
        Perform the core logic of the context operation.

        This method must be implemented by subclasses to define the specific
        operation to be performed on the given context.

        Args:
            context (ContextType): The context on which the operation is performed.

        Returns:
            None
        """
        ...

    def operate_context(self, context: ContextType):
        """
        Execute the context operation.

        Calls the subclass-implemented `_operate_context` method to perform the
        operation on the provided context.

        Args:
            context (ContextType): The context to operate on.

        Returns:
            None
        """
        return self._operate_context(context)


class SingleContextOperation(ContextOperation):
    """
    A context operation designed to work on a single context instance.

    This class provides a specialized implementation of `ContextOperation`
    tailored for operations involving individual context objects.

    Note:
        Specific behavior must be implemented in a subclass that inherits this class.
    """
    pass


class SequenceContextOperation(ContextOperation):
    """
    A context operation designed to handle sequences of context instances.

    This class extends `ContextOperation` to operate on collections of
    contexts, such as lists or other iterable structures.

    Note:
        Specific behavior must be implemented in a subclass that inherits this class.
    """
    pass

class ContextPassthough(ContextOperation):
    """
    A context operation that passes the context unchanged.

    This class is used as a default context operation for nodes when
    no specific context operation is provided.
    """

    def _operate_context(self, context):
        """
        Pass the context unchanged.

        Args:
            context (ContextType): The context to be passed through.

        Returns:
            ContextType: The unchanged context.
        """
        return context