import inspect
from typing import Any, List, Optional, Type, TypeVar, Generic, Union, Tuple

from abc import ABC, abstractmethod

from ..context_operations.context_observer import ContextObserver
from ..data_types.data_types import BaseDataType, DataCollectionType
from ..logger import Logger

# -- Type Variables --
T = TypeVar("T", bound=BaseDataType)


class BaseDataOperation(ABC, Generic[T]):
    """
    Abstract base class for all data operations in the semantic framework.

    This class defines the foundational structure for implementing data
    processing operations, ensuring consistency and extensibility.
    """

    logger: Optional[Logger]

    def __init__(self, logger: Optional[Logger] = None):
        if logger:
            self.logger = logger
        else:
            self.logger = Logger()

    @classmethod
    @abstractmethod
    def input_data_type(cls) -> Type[BaseDataType]:
        """
        Define the type of input data required for the operation.

        Returns:
            Type[BaseDataType]: The expected input data type.
        """

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieves a list of context keys that have been created by the data operation.

        This method should be implemented by subclasses to return a list of context keys
        that are generated or modified during the execution of the operation.

        Returns:
            List[str]: A list of strings representing the created keys.
        """

    @abstractmethod
    def _operation(self, data: T, *args, **kwargs) -> Any:
        """
        Core logic for the operation. Must be implemented by subclasses.

        Args:
            data (T): The input data for the operation.
            *args: Additional positional arguments for the operation.
            **kwargs: Additional keyword arguments for the operation.

        Returns:
            Any: The result of the operation.
        """

    def process(self, data: T, *args, **kwargs) -> Any:
        """
        Execute the operation with the given data.

        Args:
            data (T): The input data for the operation.
            *args: Additional positional arguments for the operation.
            **kwargs: Additional keyword arguments for the operation.

        Returns:
            Any: The result of the operation.
        """
        return self._operation(data, *args, **kwargs)

    @classmethod
    def run(cls, data, *args, **kwargs):
        return cls().process(data, *args, **kwargs)

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

    @classmethod
    def get_operation_parameter_names(cls) -> List[str]:
        """
        Retrieve the names of parameters required by the `_operation` method.

        Returns:
            List[str]: A list of parameter names (excluding `data`).
        """
        signature = inspect.signature(cls._operation)
        return [
            param.name
            for param in signature.parameters.values()
            if param.name not in {"self", "data"}
            and param.kind
            not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    @classmethod
    def get_operation_parameters_with_types(cls) -> List[Tuple[str, str]]:
        """
        Retrieve the names and type hints of parameters required by the `_operation` method.

        Returns:
            List[Tuple[str, str]]: A list of tuples (param_name, param_type).
        """
        signature = inspect.signature(cls._operation)
        return [
            (
                param.name,
                (
                    param.annotation.__name__
                    if param.annotation != param.empty
                    else "Unknown"
                ),
            )
            for param in signature.parameters.values()
            if param.name not in {"self", "data"}  # Exclude `self` and `data`
            and param.kind
            not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]


class DataAlgorithm(BaseDataOperation):
    """
    Represents a concrete data algorithm within the semantic framework.

    This class extends BaseDataOperation to incorporate contextual updates
    using a ContextObserver.

    Attributes:
        context_observer (ContextObserver): An observer for managing context updates.
    """

    context_observer: Optional[ContextObserver]

    def _notify_context_update(self, key: str, value: Any) -> None:
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

    def __init__(
        self,
        context_observer: Optional[ContextObserver] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the DataAlgorithm with a ContextObserver.

        Args:
            context_observer (ContextObserver): An observer for managing context updates.
            logger (Logger, optional): An optional logger instance.
        """
        super().__init__(logger)
        self.context_observer = context_observer

    def context_keys(self) -> List[str]:
        """
        Retrieve the list of valid context keys for the algorithm.

        This method defines the context keys that the algorithm can update
        during its execution. Subclasses need to implement this method to provide
        a list of keys that are relevant to their specific functionality.

        Returns:
            List[str]: A list of strings representing valid context keys.
        """
        return []

    def __str__(self) -> str:
        """
        Return a string representation of the instance.

        Returns:
            str: The name of the class.
        """
        return f"{self.__class__.__name__}"

    def get_created_keys(self) -> List[str]:
        """
        Retrieves a list of keys that have been created in the current context.

        Returns:
            List[str]: A list of strings representing the created keys.
        """
        return self.context_keys()

    @classmethod
    def signature_string(cls) -> str:
        """
        Returns a structured multi-line string with the algorithm signature, showing:
        - Class Name
        - Input Data Type
        - Output Data Type
        - Operation Parameter Names with Type Hints

        Returns:
            str: A formatted multi-line signature string.
        """
        input_type = cls.input_data_type().__name__
        output_type = cls.output_data_type().__name__
        param_names_with_types = cls.get_operation_parameters_with_types()

        params_section = (
            "\n\t    - "
            + "\n\t    - ".join(
                f"{name}: {ptype}" for name, ptype in param_names_with_types
            )
            if param_names_with_types
            else " None"
        )

        return f"""{cls.__name__} (DataAlgorithm)\n\tInput Type:  {input_type}\n\tOutput Type: {output_type}\n\tParameters:{params_section}\n"""

    @classmethod
    @abstractmethod
    def output_data_type(cls) -> Type[BaseDataType]:
        """
        Define the type of output data produced by the operation.

        Returns:
            Type[BaseDataType]: The expected output data type.
        """
        ...


class AlgorithmTopologyFactory:
    """
    A factory that creates algorithm classes for specific (input, output) data-type pairs.
    """

    @classmethod
    def create_algorithm(
        cls,
        input_type: Type[BaseDataType],
        output_type: Type[BaseDataType],
        class_name="GeneratedAlgorithm",
    ):
        """
        Dynamically creates a subclass of DataAlgorithm that expects `input_type`
        as input and produces `output_type` as output.

        Args:
            input_type (Type[BaseDataType]): The expected input data type (subclass of BaseDataType).
            output_type (Type[BaseDataType]): The output data type (subclass of BaseDataType).
            class_name (str): The name to give the generated class.

        Returns:
            Type[DataAlgorithm]: A new subclass of DataAlgorithm with the specified I/O data types.
        """

        methods = {}

        def input_data_type_method(self_or_cls) -> Type[BaseDataType]:
            return input_type

        def output_data_type_method(self_or_cls) -> Type[BaseDataType]:
            return output_type

        methods["input_data_type"] = classmethod(input_data_type_method)
        methods["output_data_type"] = classmethod(output_data_type_method)

        # Create a new type that extends DataAlgorithm
        generated_class = type(class_name, (DataAlgorithm,), methods)
        return generated_class


class DataProbe(BaseDataOperation):
    """
    Represents a probe operation for monitoring or inspecting data.

    This class can be extended to implement specific probing functionalities.
    """

    def __init__(self, logger=None):
        super().__init__(logger)

    def get_created_keys(self) -> List[str]:
        """ """
        return []

    @classmethod
    def signature_string(cls) -> str:
        """
        Returns a structured multi-line string with the algorithm signature, showing:
        - Class Name
        - Input Data Type
        - Output Data Type
        - Operation Parameter Names with Type Hints

        Returns:
            str: A formatted multi-line signature string.
        """
        input_type = cls.input_data_type().__name__
        param_names_with_types = cls.get_operation_parameters_with_types()

        params_section = (
            "\n\t    - "
            + "\n\t    - ".join(
                f"{name}: {ptype}" for name, ptype in param_names_with_types
            )
            if param_names_with_types
            else " None"
        )

        return f"""{cls.__name__} (DataProbe)\n\tInput Type:  {input_type}\n\tParameters:{params_section}\n"""


BaseType = TypeVar("BaseType", bound=BaseDataType)


class DataCollectionProbe(BaseDataOperation, Generic[BaseType]):
    """
    A probe for inspecting or monitoring data collections.

    This class extends `BaseDataOperation` to define operations that accept
    `DataCollectionType`, allowing the extraction of observables.

    Methods:
        input_data_type: Returns the expected input data type (`DataCollectionType`).
    """

    def __init__(self, logger=None):
        super().__init__(logger)

    @classmethod
    def input_data_type(cls) -> Type[DataCollectionType]:
        """
        Specifies the input data type for the probe.

        Returns:
            Type[DataCollectionType]: The expected input data type.
        """
        return DataCollectionType


FeatureType = TypeVar("FeatureType")  # The extracted feature type (e.g., float)


# For convenience, define a TypeVar for the data collection base
CollectionBaseT = TypeVar("CollectionBaseT", bound=BaseDataType)


class FeatureExtractorProbeWrapper(DataProbe):
    """
    A wrapper probe that extracts only the required parameter(s) from a dictionary-based probe.

    This allows using a probe that returns a full dictionary but only passing the required values
    to the next stage of processing (e.g., fitting a model).
    """

    def __init__(
        self, feature_probe: Type[DataProbe], param_key: Union[str, Tuple[str, ...]]
    ):
        """
        Initializes the FeatureExtractorWrapperProbe with a specified parameter key or keys.

        Parameters:
        ----------
        feature_probe : Type[DataProbe]
            The original probe that returns a dictionary of results.
        param_key : str or tuple of str
            The key(s) of the parameter(s) to extract from the probe output.
        """
        self.param_key = param_key
        self.feature_probe = feature_probe()

    def input_data_type(self):
        """Returns the input data type required by the wrapped probe."""
        return self.feature_probe.input_data_type()

    def _operation(self, data) -> Union[Any, Tuple[Any, ...]]:
        """
        Processes the input data through the original probe and extracts the required parameter(s).

        Args:
            data (Any): The input data to be processed by the probe.

        Returns:
            Union[Any, Tuple[Any, ...]]: Extracted value(s) from the probe output.
        """
        fitted_params = self.feature_probe.process(data)

        if isinstance(self.param_key, tuple):
            return tuple(fitted_params[key] for key in self.param_key)

        return fitted_params[self.param_key]
