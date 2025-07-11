# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from abc import abstractmethod
from semantiva.context_processors.context_observer import _ContextObserver
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.data_types import BaseDataType
from semantiva.logger import Logger

T = TypeVar("T", bound=BaseDataType)


class _BaseDataProcessor(_SemantivaComponent, Generic[T]):
    """Abstract base class for data processing algorithms in Semantiva."""

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
        Define the expected type of input data for processing.

        Returns:
            Type[BaseDataType]: The required input data type.
        """

    @classmethod
    @abstractmethod
    def get_created_keys(cls) -> List[str]:
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
    def _define_metadata(cls) -> Dict[str, Any]:
        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._process_logic, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "BaseDataProcessor",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            if hasattr(cls, "output_data_type"):
                component_metadata["output_data_type"] = cls.output_data_type().__name__
        except Exception:
            # no binding available at this abstract level
            pass

        return component_metadata


class DataOperation(_BaseDataProcessor):
    """A data processor that applies computational transformations to input data while managing context updates."""

    context_observer: Optional[_ContextObserver]

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        # Retrieve the parameter signatures for the _process_logic method
        # and exclude the 'self' and 'data' parameters from the metadata
        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._process_logic, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "DataOperation",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            component_metadata["output_data_type"] = cls.output_data_type().__name__
        except Exception:
            # no binding available at this abstract level
            pass

        # Define the metadata for the DataOperation

        return component_metadata

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
        context_observer: Optional[_ContextObserver] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a `DataOperation` with an optional `_ContextObserver`.

        Args:
            context_observer (Optional[_ContextObserver]): An observer for managing
                context updates. Defaults to None.
            logger (Optional[Logger]): A logger instance for tracking execution
                details. Defaults to None.
        """
        super().__init__(logger)
        self.context_observer = context_observer

    @classmethod
    def context_keys(cls) -> List[str]:
        """
        Retrieve the list of valid context keys for the data operation.

        This method defines the context keys that the data operation can update
        during its execution. Subclasses need to implement this method to provide
        a list of keys that are relevant to their specific functionality.

        Returns:
            List[str]: A list of context keys that an operation can update.
        """
        return []

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys created by the data operation.

        Returns:
            List[str]: A list of context keys created or modified by the operation.
        """
        return cls.context_keys()

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
        param_names_with_types = cls._retrieve_parameter_signatures(
            cls._process_logic, ["self", "data"]
        )

        params_section = (
            "\n\t    - "
            + "\n\t    - ".join(
                f"{name}: {ptype}" for name, ptype in param_names_with_types
            )
            if param_names_with_types
            else " None"
        )

        return f"""{cls.__name__} (DataOperation)\n\tInput Type:  {input_type}\n\tOutput Type: {output_type}\n\tParameters:{params_section}\n"""

    @classmethod
    @abstractmethod
    def output_data_type(cls) -> Type[BaseDataType]:
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
        class_name: str,
    ) -> type[DataOperation]:
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

        def input_data_type_method(cls) -> type[BaseDataType]:
            return input_type

        def output_data_type_method(cls) -> type[BaseDataType]:
            return output_type

        methods["input_data_type"] = classmethod(input_data_type_method)
        methods["output_data_type"] = classmethod(output_data_type_method)

        # Create a new type that extends DataOperation
        generated_class = type(class_name, (DataOperation,), methods)
        return generated_class


class DataProbe(_BaseDataProcessor):
    """DataProbe analyzes input data without modifying it."""

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys created by the data probe.

        Returns:
            List[str]: A list of context keys created or modified by the data probe.
        """

        return []

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        # Retrieve the parameter signatures for the _process_logic method
        # and exclude the 'self' and 'data' parameters from the metadata
        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._process_logic, excluded_parameters
            )
        ]

        # Define the metadata for the DataProbe
        component_metadata = {
            "component_type": "DataProbe",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            component_metadata["input_data_type"] = cls.input_data_type().__name__
        except Exception:
            # no binding available at this abstract level
            pass

        return component_metadata

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
        param_names_with_types = cls._retrieve_parameter_signatures(
            cls._process_logic, ["self", "data"]
        )

        params_section = (
            "\n\t    - "
            + "\n\t    - ".join(
                f"{name}: {ptype}" for name, ptype in param_names_with_types
            )
            if param_names_with_types
            else " None"
        )

        return f"""{cls.__name__} (DataProbe)\n\tInput Type:  {input_type}\n\tParameters:{params_section}\n"""
