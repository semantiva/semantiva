import inspect
from typing import Any, List, Optional
from abc import ABC, abstractmethod
from ..context_operations.context_observer import ContextObserver
from ..data_types.data_types import BaseDataType


class BaseDataOperation(ABC):
    """
    Abstract base class for all data operations in the semantic framework.

    This class defines the foundational structure for implementing data
    processing operations, ensuring consistency and extensibility.
    """

    @classmethod
    @abstractmethod
    def input_data_type(cls) -> BaseDataType:
        """
        Define the type of input data required for the operation.

        Returns:
            type: The expected input data type.
        """
        pass

    @abstractmethod
    def _operation(self, data: BaseDataType, *args, **kwargs) -> Any:
        """
        Core logic for the operation. Must be implemented by subclasses.

        Args:
            data (BaseDataType): The input data for the operation.
            *args: Additional positional arguments for the operation.
            **kwargs: Additional keyword arguments for the operation.

        Returns:
            Any: The result of the operation.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def process(self, data: BaseDataType, *args, **kwargs) -> Any:
        """
        Execute the operation with the given data.

        Args:
            data (BaseDataType): The input data for the operation.
            *args: Additional positional arguments for the operation.
            **kwargs: Additional keyword arguments for the operation.

        Returns:
            Any: The result of the operation.
        """
        return self._operation(data, *args, **kwargs)

    def __call__(self, data: Any, *args, **kwargs) -> Any:
        """
        Allow the operation to be called as a callable object.

        Args:
            data (Any): The input data for the operation.
            *args: Additional positional arguments for the operation.
            **kwargs: Additional keyword arguments for the operation.

        Returns:
            Any: The result of the operation.
        """
        return self.process(data, *args, **kwargs)

    def get_operation_parameter_names(self) -> List[str]:
        """
        Retrieve the names of parameters required by the `_operation` method.

        Returns:
            List[str]: A list of parameter names (excluding `data`).
        """
        signature = inspect.signature(self._operation)
        return [
            param.name
            for param in signature.parameters.values()
            if param.name != "data"
        ]


class DataAlgorithm(BaseDataOperation):
    """
    Represents a concrete data algorithm within the semantic framework.

    This class extends BaseDataOperation to incorporate contextual updates
    using a ContextObserver.

    Attributes:
        context_observer (ContextObserver): An observer for managing context updates.
    """

    context_observer: ContextObserver

    @classmethod
    @abstractmethod
    def output_data_type(cls) -> BaseDataType:
        """
        Define the type of data output by the algorithm.

        Returns:
            BaseDataType: The expected output data type.
        """
        pass

    def _notify_context_update(self, key: str, value: Any):
        """
        Notify the context observer about a context update.

        Args:
            key (str): The key associated with the context update.
            value (Any): The value to update in the context.
        """
        self.context_observer.context[key] = value

    def __init__(self, context_observer: Optional[ContextObserver] = None):
        """
        Initialize the DataAlgorithm with a ContextObserver.

        Args:
            context_observer (ContextObserver): An observer for managing context updates.
        """
        self.context_observer = context_observer


class DataProbe(BaseDataOperation):
    """
    Represents a probe operation for monitoring or inspecting data.

    This class can be extended to implement specific probing functionalities.
    """

    pass
