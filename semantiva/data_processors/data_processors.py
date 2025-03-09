import inspect
from typing import Any, List, Optional, Type, TypeVar, Generic, Union, Tuple

from abc import ABC, abstractmethod

from ..context_processors.context_observer import ContextObserver
from ..data_types.data_types import BaseDataType, DataCollectionType
from ..logger import Logger

# -- Type Variables --
T = TypeVar("T", bound=BaseDataType)


class BaseDataProcessor(ABC, Generic[T]):
    """
    Abstract base class for all data processors in Semantiva.

    This class defines a standardized structure for implementing data
    processing tasks, ensuring consistency and extensibility across different
    types of data transformations and analyses.
    """

    logger: Optional[Logger]

    def __init__(self, logger: Optional[Logger] = None):
        if logger:
            self.logger = logger
        else:
            self.logger = Logger()

    @staticmethod
    @abstractmethod
    def input_data_type() -> Type[BaseDataType]:
        """
        Define the expected type of input data for processing.

        Returns:
            Type[BaseDataType]: The required input data type.
        """

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieves a list of context keys generated during processing.

        This method should be implemented by subclasses to return a list of
        context keys that are produced or modified during execution.

        Returns:
            List[str]: A list of generated context keys.
        """

    @abstractmethod
    def _process_logic(self, data: T, *args, **kwargs) -> Any:
        """
        Core processing logic. Must be implemented by subclasses.

        Args:
            data (T): The input data to be processed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The result of the processing.
        """

    def process(self, data: T, *args, **kwargs) -> Any:
        """
        Execute the processing logic on the given data.

        Args:
            data (T): The input data for processing.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The processed output.
        """
        return self._process_logic(data, *args, **kwargs)

    @classmethod
    def run(cls, data, *args, **kwargs):
        return cls().process(data, *args, **kwargs)

    def __call__(self, data: Any, *args, **kwargs) -> Any:
        """
        Allow the processor to be invoked like a callable function.

        Args:
            data (Any): The input data for processing.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The processed output.
        """
        return self.process(data, *args, **kwargs)

    @classmethod
    def get_processing_parameter_names(cls) -> List[str]:
        """
        Retrieve the names of parameters required by the `_process_logic` method.

        Returns:
            List[str]: A list of parameter names (excluding `self` and `data`).
        """
        signature = inspect.signature(cls._process_logic)
        return [
            param.name
            for param in signature.parameters.values()
            if param.name not in {"self", "data"}
            and param.kind
            not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__name__}"

    @classmethod
    def get_processing_parameters_with_types(cls) -> List[Tuple[str, str]]:
        """
        Retrieve the names and type hints of parameters required by the `_process_logic` method.

        Returns:
            List[Tuple[str, str]]: A list of tuples (param_name, param_type).
        """
        signature = inspect.signature(cls._process_logic)
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


class DataOperation(BaseDataProcessor):
    """
    A data processing component within Semantiva that modifies input data.

    `DataOperation` extends `BaseDataProcessor` to provide transformation
    capabilities while integrating with a `ContextObserver` for managing
    context updates. Unlike `DataProbe`, which analyzes data without
    modification, `DataOperation` applies computational transformations to
    produce a modified output.

    Attributes:
        context_observer (Optional[ContextObserver]): An optional observer for tracking
            and managing context updates during processing.
    """

    context_observer: Optional[ContextObserver]

    def _notify_context_update(self, key: str, value: Any) -> None:
        """
        Notify the context observer about a context modification.

        This method updates the context state with a new value.

        Args:
            key (str): The context key being updated.
            value (Any): The new value associated with the context key.

        Raises:
            KeyError: If the provided key is not a registered context key.
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
        Initialize a `DataOperation` with an optional `ContextObserver`.

        Args:
            context_observer (Optional[ContextObserver]): An observer for managing
                context updates. Defaults to None.
            logger (Optional[Logger]): A logger instance for tracking execution
                details. Defaults to None.
        """
        super().__init__(logger)
        self.context_observer = context_observer

    def context_keys(self) -> List[str]:
        """
        Retrieve the list of valid context keys for the data operation.

        This method defines the context keys that the data operation can update
        during its execution. Subclasses need to implement this method to provide
        a list of keys that are relevant to their specific functionality.

        Returns:
            List[str]: A list of context keys that an operation can update.
        """
        return []

    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys created by the data operation.

        Returns:
            List[str]: A list of context keys created or modified by the operation.
        """
        return self.context_keys()

    @classmethod
    def signature_string(cls) -> str:
        """
        Generate a structured summary of the data operation signature.

        This includes:
        - Class Name
        - Input Data Type
        - Output Data Type
        - Processing Parameters with Type Hints

        Returns:
            str: A formatted multi-line string representing the operation signature.
        """
        input_type = cls.input_data_type().__name__
        output_type = cls.output_data_type().__name__
        param_names_with_types = cls.get_processing_parameters_with_types()

        params_section = (
            "\n\t    - "
            + "\n\t    - ".join(
                f"{name}: {ptype}" for name, ptype in param_names_with_types
            )
            if param_names_with_types
            else " None"
        )

        return f"""{cls.__name__} (DataOperation)\n\tInput Type:  {input_type}\n\tOutput Type: {output_type}\n\tParameters:{params_section}\n"""

    @staticmethod
    @abstractmethod
    def output_data_type() -> Type[BaseDataType]:
        """
        Define the type of output data produced by this operation.

        Subclasses must implement this method to specify the expected
        output type after processing.

        Returns:
            Type[BaseDataType]: The output data type produced by the operation.
        """
        ...


class OperationTopologyFactory:
    """
    A factory that creates data operation classes for specific (input, output) data-type pairs.
    """

    @classmethod
    def create_data_operation(
        cls,
        input_type: Type[BaseDataType],
        output_type: Type[BaseDataType],
        class_name="GeneratedOperation",
    ):
        """
        Dynamically creates a subclass of DataOperation that expects `input_type`
        as input and produces `output_type` as output.

        Args:
            input_type (Type[BaseDataType]): The expected input data type (subclass of BaseDataType).
            output_type (Type[BaseDataType]): The output data type (subclass of BaseDataType).
            class_name (str): The name to give the generated class.

        Returns:
            Type[DataOperation]: A new subclass of DataOperation with the specified I/O data types.
        """

        methods: dict = {}

        def input_data_type_method() -> Type[BaseDataType]:
            return input_type

        def output_data_type_method() -> Type[BaseDataType]:
            return output_type

        methods["input_data_type"] = staticmethod(input_data_type_method)
        methods["output_data_type"] = staticmethod(output_data_type_method)

        # Create a new type that extends DataOperation
        generated_class = type(class_name, (DataOperation,), methods)
        return generated_class


class DataProbe(BaseDataProcessor):
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
        Returns a structured multi-line string with the data operation signature, showing:
        - Class Name
        - Input Data Type
        - Output Data Type
        - Operation Parameter Names with Type Hints

        Returns:
            str: A formatted multi-line signature string.
        """
        input_type = cls.input_data_type().__name__
        param_names_with_types = cls.get_processing_parameters_with_types()

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


class DataCollectionProbe(BaseDataProcessor, Generic[BaseType]):
    """
    A probe for inspecting or monitoring data collections.

    This class extends `BaseDataProcessor` to define operations that accept
    `DataCollectionType`, allowing the extraction of observables.

    Methods:
        input_data_type: Returns the expected input data type (`DataCollectionType`).
    """

    def __init__(self, logger=None):
        super().__init__(logger)

    @staticmethod
    def input_data_type() -> Type[DataCollectionType]:
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

    def _process_logic(self, data) -> Union[Any, Tuple[Any, ...]]:
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
