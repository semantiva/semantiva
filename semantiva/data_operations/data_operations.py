import inspect
from typing import Any, List, Optional, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from ..context_operations.context_observer import ContextObserver
from ..data_types.data_types import BaseDataType


T = TypeVar("T", bound=BaseDataType)


class BaseDataOperation(ABC, Generic[T]):
    """
    Abstract base class for all data operations in the semantic framework.

    This class defines the foundational structure for implementing data
    processing operations, ensuring consistency and extensibility.
    """

    @classmethod
    @abstractmethod
    def input_data_type(cls) -> Type[BaseDataType]:
        """
        Define the type of input data required for the operation.

        Returns:
            type: The expected input data type.
        """
        return BaseDataType

    @classmethod
    def output_data_type(cls) -> Type[BaseDataType]:
        """
        Define the type of input data required for the operation.

        Returns:
            type: The expected input data type.
        """
        return cls.input_data_type()

    @abstractmethod
    def _operation(self, data: T, *args, **kwargs) -> Any:
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

    def process(self, data: T, *args, **kwargs) -> Any:
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
            and param.kind
            not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]

    def __str__(self):
        return f"{self.__class__.__name__}"


class DataAlgorithm(BaseDataOperation):
    """
    Represents a concrete data algorithm within the semantic framework.

    This class extends BaseDataOperation to incorporate contextual updates
    using a ContextObserver.

    Attributes:
        context_observer (ContextObserver): An observer for managing context updates.
    """

    context_observer: Optional[ContextObserver]

    def _notify_context_update(self, key: str, value: Any):
        """
        Notify the context observer about a context update.

        Args:
            key (str): The key associated with the context update.
            value (Any): The value to update in the context.
        """
        if key not in self.context_keys():
            raise KeyError(f"Invalid context key '{key}' for {self.__class__.__name__}")
        if self.context_observer:
            self.context_observer.observer_context.set_value(key, value)

    def __init__(self, context_observer: Optional[ContextObserver] = None):
        """
        Initialize the DataAlgorithm with a ContextObserver.

        Args:
            context_observer (ContextObserver): An observer for managing context updates.
        """
        self.context_observer = context_observer

    def context_keys(self) -> List[str]:
        """
        Retrieve the list of valid context keys for the algorithm.

        This method defines the context keys that the algorithm can update
        during its execution. Subclasses need to implement this method to provide
        a list of keys that are relevant to their specific functionality.

        Returns:
            List[str]: A list of strings representing valid context keys.


        Example:
            For an algorithm that generates a 'status' key and an 'error_count' key
            in the context, this method should return:
            ["status", "error_count"]
        """
        return []

    def __str__(self):
        return f"{self.__class__.__name__}"


class DataProbe(BaseDataOperation):
    """
    Represents a probe operation for monitoring or inspecting data.

    This class can be extended to implement specific probing functionalities.
    """


class AlgorithmTopologyFactory:
    """
    A factory that creates algorithm classes for specific (input, output) data-type pairs.
    """

    @classmethod
    def create_algorithm(cls, input_type, output_type, class_name="GeneratedAlgorithm"):
        """
        Dynamically creates a subclass of DataAlgorithm that expects `input_type`
        as input and produces `output_type` as output.

        Args:
            input_type (type): The expected input data type (subclass of BaseDataType).
            output_type (type): The output data type (subclass of BaseDataType).
            class_name (str): The name to give the generated class.

        Returns:
            type: A new subclass of DataAlgorithm with the specified I/O data types.
        """

        # Define a dictionary of class-level methods for the new type
        methods = {}

        def input_data_type_method(self_or_cls):
            return input_type

        def output_data_type_method(self_or_cls):
            return output_type

        methods["input_data_type"] = classmethod(input_data_type_method)
        methods["output_data_type"] = classmethod(output_data_type_method)

        # Create a new type that extends DataAlgorithm
        generated_class = type(class_name, (DataAlgorithm,), methods)
        return generated_class
