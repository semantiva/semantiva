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
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def output_data_type(cls) -> Type[BaseDataType]:
        """
        Define the type of output data produced by the operation.

        Returns:
            Type[BaseDataType]: The expected output data type.
        """
        return cls.input_data_type()

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

    def __str__(self) -> str:
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
        return f"{self.__class__.__name__}"


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


class DataCollectionFeatureExtractionProbe(
    DataCollectionProbe[BaseType], Generic[BaseType, FeatureType]
):
    """
    A probe that extracts features from a data collection.

    This probe processes a `DataCollectionType`, applying a feature extraction operation
    (provided by an individual `DataProbe`) to each element in the collection. The result
    is a list of extracted feature values.

    Attributes:
        feature_extractor (DataProbe): A probe responsible for extracting a single feature
                                       from individual elements.
    """

    def __init__(self, feature_extractor: DataProbe, logger: Optional[Logger] = None):
        """
        Initializes the `DataCollectionFeatureExtractionProbe` with a feature extractor.

        Args:
            feature_extractor (DataProbe): A probe that extracts a feature from individual elements.
        """
        super().__init__(logger=logger)
        self.feature_extractor = feature_extractor

    def _operation(self, data: DataCollectionType) -> List[FeatureType]:
        """
        Extracts features from each element in the input data collection.

        Args:
            data (DataCollectionType): The input data collection.

        Returns:
            List[FeatureType]: A list of extracted feature values.
        """
        return [self.feature_extractor.process(item) for item in data]


# For convenience, define a TypeVar for the data collection base
CollectionBaseT = TypeVar("CollectionBaseT", bound=BaseDataType)

# ExtractedFeatureType -> Extracted feature type (dependent variable)
ExtractedFeatureType = TypeVar("ExtractedFeatureType")


def create_data_collection_feature_extraction_probe(
    feature_extractor: DataProbe,
    class_name: str = "GeneratedDataCollectionFeatureExtractionProbe",
):
    """
    Factory function to create a `DataCollectionFeatureExtractionProbe` class using
    dynamic type creation.

    This ensures that an individual feature extraction probe can be applied
    to a full data collection.

    Args:
        feature_extractor (DataProbe): The feature extraction probe for individual elements.
        class_name (str): The name to give the dynamically generated class.

    Returns:
        Type[DataCollectionFeatureExtractionProbe[CollectionBaseT, ExtractedFeatureType]]:
            A dynamically generated subclass of DataCollectionFeatureExtractionProbe.
    """

    # Define a new class dynamically
    class DynamicFeatureExtractionProbe(
        DataCollectionFeatureExtractionProbe[CollectionBaseT, ExtractedFeatureType]
    ):
        def __init__(self, logger: Optional[Logger] = None) -> None:
            """
            Initializes the dynamically created DataCollectionFeatureExtractionProbe.

            Args:
                logger (Optional[Logger]): Logger instance (optional).
            """
            super().__init__(feature_extractor=feature_extractor, logger=logger)

    # Assign the provided class name dynamically
    DynamicFeatureExtractionProbe.__name__ = class_name
    DynamicFeatureExtractionProbe.__qualname__ = class_name

    return DynamicFeatureExtractionProbe


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
