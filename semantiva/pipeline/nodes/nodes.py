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

from typing import List, Any, Dict, Optional, Type
from typing_extensions import override
from abc import abstractmethod
from semantiva.context_processors import ContextProcessor
from semantiva.data_processors.data_processors import (
    _BaseDataProcessor,
    DataOperation,
    DataProbe,
    ParameterInfo,
    _NO_DEFAULT,
)
from semantiva.context_processors.context_observer import _ContextObserver

from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.data_types import NoDataType
from semantiva.logger import Logger
from ..payload_processors import _PayloadProcessor
from ..payload import Payload


class _PipelineNode(_PayloadProcessor):
    """
    Base node class for wrapping data or context processors.
    """

    processor: _BaseDataProcessor | ContextProcessor
    processor_config: Dict

    @abstractmethod
    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        """
        Process a single data item with its corresponding context.
        Args:
            payload (Payload): Payload containing data and context.
        Returns:
            Payload: The processed data and updated context.
        """


class _DataNode(_PipelineNode):
    """
    A node that wraps a data processor.
    """

    processor: _BaseDataProcessor

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _DataNode with a specific data processor and its configuration.

        Args:
            processor (Type[_BaseDataProcessor]): The class of the data processor associated with this node.
            processor_config (Optional[Dict]): Configuration parameters for the data processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} ({processor.__name__})"
        )
        self.processor_config = {} if processor_config is None else processor_config
        self.logger.debug(f"self = {self}, logger = {self.logger}")
        self.processor = (
            processor(self, self.logger)
            if issubclass(processor, DataOperation)
            else processor(logger=self.logger)
        )

    @classmethod
    @abstractmethod
    def input_data_type(cls):
        """
        Retrieve the expected input data type for the data processor.

        Returns:
            Type: The expected input data type for the data processor.
        """

    @classmethod
    @abstractmethod
    def output_data_type(cls):
        """
        Retrieve the output data type of the node.
        """

    def _get_processor_parameters(self, context: ContextType) -> dict:
        """
        Retrieve the parameters required for the associated data processor.

        Args:
            context (ContextType): Contextual information used to resolve parameter values.

        Returns:
            dict: A dictionary mapping parameter names to their values.
        """
        parameter_names = self.processor.get_processing_parameter_names()
        parameters = {}
        for name in parameter_names:
            parameters[name] = self._fetch_parameter_value(name, context)
        return parameters

    def _fetch_parameter_value(self, name: str, context: ContextType) -> Any:
        """
        Retrieve a parameter value based on the node's processor configuration or the context.

        Args:
            name (str): The name of the parameter to retrieve.
            context (ContextType): Contextual information used to resolve parameter values.

        Returns:
            Any: The value of the parameter, with `processor_config` taking precedence over the context.
        """
        if name in self.processor_config:
            return self.processor_config[name]
        if name in context.keys():
            return context.get_value(name)

        metadata = self.processor.__class__.get_metadata()
        param_info = metadata.get("parameters", {}).get(name)
        if isinstance(param_info, ParameterInfo):
            default = param_info.default
        elif isinstance(param_info, dict):
            default = param_info.get("default", _NO_DEFAULT)
        else:
            default = _NO_DEFAULT

        if default is not _NO_DEFAULT:
            return default
        raise KeyError(
            f"Unable to resolve parameter '{name}' from context, node configuration, or defaults."
        )

    def __str__(self) -> str:
        """
        Return a string representation of the node.

        Returns:
            str: A string summarizing the node's attributes and execution summary.
        """
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     data_processor={self.processor},\n"
            f"     processor_config={self.processor_config},\n"
            f"     execution summary: {self.stop_watch}\n"
            f")"
        )

    @classmethod
    @abstractmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys created or updated by the data processor.

        Returns:
            List[str]: A list of context keys that the data processor crestes or modifies
                       as a result of execution.
        """

    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        """
        Process a single data item with its corresponding single context.

        Args:
            payload (Payload): The input payload.

        Returns:
            Payload: The processed data and the updated context.
        """

        data = payload.data
        context = payload.context
        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        output_data = self.processor.process(data, **parameters)

        return Payload(output_data, self.observer_context)

    def _process(self, payload: Payload) -> Payload:
        """
        Process payload.

        This method processes the given payload using the configured data processor and updates the execution context.
        It supports both single payload objects and collections of payloads by applying the appropriate processing strategy
        based on the input types.

        Parameters:
            payload (Payload): The payload to be processed.
            execution_context (ContextType): The context at this step, which may be a singular context or a collection of contexts.

        Returns:
            Payload: The processed payload with updated context.

        Raises:
            ValueError:
            If a single payload is paired with a collection context.
            TypeError
            If the payload type is incompatible with the expected input type for the data processor.
        """

        result_data, result_context = payload.data, payload.context
        input_type = self.processor.input_data_type()

        if issubclass(type(result_data), input_type):
            return self._process_single_item_with_context(
                Payload(result_data, result_context)
            )
        else:
            raise TypeError(
                f"Incompatible data type for Node {self.processor.__class__.__name__} "
                f"expected {input_type}, but received {type(result_data)}."
            )


class _PayloadSourceNode(_DataNode):
    """
    A node that wraps a PayloadSource.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _PayloadSourceNode with the specified payload source.

        Args:
            processor (Type[PayloadSource]): The payload source class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            processor,
            processor_parameters,
            logger,
        )

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "PayloadSourceNode",
            "wraps_component_type": "PayloadSource",
            "input_data_type": "NoDataType",
        }

        try:
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["output_data_type"] = cls.output_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            pass
        return component_metadata

    @classmethod
    def input_data_type(cls):
        """
        Retrieve NoDataType.

        Returns:
            NoDataType: Represents that no data is consumed by this node.
        """
        return NoDataType

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the node's output data type.
        """
        return cls.processor.output_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        # PayloadSource processors have injected_context_keys method
        if hasattr(cls.processor, "injected_context_keys"):
            return cls.processor.injected_context_keys()
        return []

    @override
    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        """
        Process a single data item with its corresponding single context.

        Args:
            payload (Payload): A single data/context pair.

        Returns:
            Payload: The processed data and updated context.
        """

        data = payload.data
        context = payload.context
        # Save the current context to be used by the processor
        parameters = self._get_processor_parameters(payload.context)
        loaded_data = self.processor.process(data, **parameters)
        loaded_context = self.observer_context

        # Merge context and loaded_context
        for key, value in loaded_context.items():
            if key in context.keys():
                raise KeyError(f"Key '{key}' already exists in the context.")
            context.set_value(key, value)
        return Payload(loaded_data, context)


class _PayloadSinkNode(_DataNode):
    """
    A node that wraps a PayloadSink.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _PayloadSinkNode with the specified payload sink.

        Args:
            processor (Type[PayloadSink]): The payload sink class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            processor,
            processor_parameters,
            logger,
        )

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "PayloadSinkNode",
            "wraps_component_type": "PayloadSink",
        }

        try:
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            component_metadata["output_data_type"] = (
                cls.input_data_type().__name__
            )  # Same as input

        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def input_data_type(cls):
        """
        Retrieve the data type that will be consumed by the processor.

        Returns:
            Type: The data type that will be consumed by the processor.
        """
        return cls.processor.input_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        return []

    @classmethod
    def output_data_type(cls):
        """
        Retrieve this node's output data type. Payload sink nodes act as data passthough.
        """
        return cls.input_data_type()


class _DataSinkNode(_DataNode):
    """
    A node that wraps a DataSink.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _DataSinkNode with the specified data sink.

        Args:
            processor (Type[_BaseDataProcessor]): The base data processor for the _DataSinkNode.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            processor,
            processor_parameters,
            logger,
        )

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "DataSinkNode",
            "wraps_component_type": "DataSink",
        }

        try:
            assert hasattr(cls.processor, "_send_data")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            component_metadata["output_data_type"] = (
                cls.input_data_type().__name__
            )  # Same as input
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def input_data_type(cls):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return cls.processor.input_data_type()

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return cls.input_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        return []


class _DataSourceNode(_DataNode):
    """
    A node that wraps a DataSource.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _DataSourceNode with the specified data source.

        Args:
            processor (Type[_BaseDataProcessor]): The _BaseDataProcessor for the _DataSourceNode.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            processor,
            processor_parameters,
            logger,
        )

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "DataSourceNode",
            "wraps_component_type": "DataSource",
            "input_data_type": "NoDataType",
        }

        try:
            assert hasattr(cls.processor, "_get_data")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["output_data_type"] = cls.output_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def input_data_type(cls):
        """
        Retrieve the data type that will be consumed by the processor.

        Returns:
            Type: The data type that will be consumed by the processor.
        """
        return NoDataType

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return cls.processor.output_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
                    as a result of execution.
        """
        return []


class _DataOperationNode(_DataNode):
    """
    A node that wraps a DataOperation.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize an _DataOperationNode with the specified data algorithm.

        Args:
            processor (Type[_BaseDataProcessor]): The base data processor for this node.
            processor_parameters (Optional[Dict]): Initial configuration for processor parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        processor_parameters = (
            {} if processor_parameters is None else processor_parameters
        )
        super().__init__(processor, processor_parameters, logger)

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "DataOperationNode",
            "wraps_component_type": "DataOperation",
        }

        try:
            # DataOperation subclasses expose input/output data type classmethods
            assert hasattr(cls.processor, "input_data_type")
            assert hasattr(cls.processor, "output_data_type")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            component_metadata["output_data_type"] = cls.output_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def input_data_type(cls):
        """
        Retrieve input data type of the data processor.

        """
        return cls.processor.input_data_type()

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the node's output data type. The request is delegated to the node's data processor.

        Returns:
            Type: The node output data type.
        """
        return cls.processor.output_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
                    as a result of execution.
        """
        return cls.processor.get_created_keys()


class _DataOperationContextInjectorProbeNode(_DataOperationNode):
    """A node that runs a :class:`DataOperation`, stores its output in the
    context under a specified keyword, and forwards the original data."""

    context_keyword: str

    def __init__(
        self,
        processor: Type[DataOperation],
        context_keyword: str,
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self.context_keyword = context_keyword
        super().__init__(processor, processor_parameters, logger)

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "DataOperationContextInjectorProbeNode",
            "wraps_component_type": "DataOperation",
        }

        try:
            assert hasattr(cls.processor, "_send_data")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            component_metadata["output_data_type"] = cls.output_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def output_data_type(cls):
        """The output type matches the input type as data is passed through."""

        return cls.input_data_type()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """Return context keys injected by this node."""
        return [cls.context_keyword]

    @override
    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        data = payload.data
        context = payload.context
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        result = self.processor.process(data, **parameters)
        _ContextObserver.update_context(context, self.context_keyword, result)
        return Payload(data, context)


class _ProbeNode(_DataNode):
    """
    A node that wraps a DataProbe.
    """

    @classmethod
    def input_data_type(cls):
        """
        Provides the input data type for the probe node, which is the same as the processor's input data type..

        Returns:
            Type: The input data type for the probe node.
        """

        return cls.processor.input_data_type()

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the node's output data type. The output data type is the same as the input data type for probe nodes.

        Returns:
            Type: The node's output data type.
        """
        return cls.input_data_type()


class _ProbeContextInjectorNode(_ProbeNode):
    """
    A node that wraps a DataProbe and injects the probe result into the context with the specified keyword.
    """

    context_keyword: str

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        context_keyword: str,
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _ProbeContextInjectorNode with the specified data processor and context keyword.

        Args:
            processor (Type[_BaseDataProcessor]): The data probe class for this node.
            context_keyword (str): The keyword used to inject the probe result into the context.
            processor_parameters (Optional[Dict]): Operation configuration parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.

        Raises:
            ValueError: If `context_keyword` is not provided or is not a non-empty string.
        """
        self.context_keyword = context_keyword
        super().__init__(processor, processor_parameters, logger)

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "ProbeContextInjectorNode",
            "wraps_component_type": "DataProbe",
        }

        try:
            # Probe processors expose an input_data_type classmethod
            assert hasattr(cls.processor, "input_data_type")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            # The output data type is the same as the input data type for probe nodes
            component_metadata["output_data_type"] = cls.input_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
            as a result of execution.
        """
        return [cls.context_keyword]

    def __str__(self) -> str:
        """
        Return a string representation of the _ProbeContextInjectorNode.

        Returns:
            str: A string summarizing the node's attributes and execution summary.
        """
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     processor={self.processor},\n"
            f"     context_keyword={self.context_keyword},\n"
            f"     processor_config={self.processor_config},\n"
            f"     execution summary: {self.stop_watch}\n"
            f")"
        )

    @override
    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        """
        Process a single data item and inject the probe result into the context.

        Args:
            payload (Payload): The input payload.

        Returns:
            Payload: The unchanged data and the updated context with the probe result.
        """

        data = payload.data
        context = payload.context
        parameters = self._get_processor_parameters(context)
        probe_result = self.processor.process(data, **parameters)
        if isinstance(context, ContextCollectionType):
            for index, p_item in enumerate(probe_result):
                _ContextObserver.update_context(
                    context, self.context_keyword, p_item, index=index
                )
        else:
            _ContextObserver.update_context(context, self.context_keyword, probe_result)

        return Payload(data, context)


class _ProbeResultCollectorNode(_ProbeNode):
    """
    A node that wraps a DataProbe and collects probe results.
    """

    def __init__(
        self,
        processor: Type[_BaseDataProcessor],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a _ProbeResultCollectorNode with the specified data probe.

        Args:
            processor (Type[DataProbe]): The data probe class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for diagnostic output. Defaults to None.
        """
        super().__init__(processor, processor_parameters, logger)
        self._probed_data: List[Any] = []

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "ProbeResultCollectorNode",
            "wraps_component_type": "DataProbe",
        }

        try:
            # Probe processors expose an input_data_type classmethod
            assert hasattr(cls.processor, "input_data_type")
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["input_data_type"] = cls.input_data_type().__name__
            # The output data type is the same as the input data type for probe nodes
            component_metadata["output_data_type"] = cls.input_data_type().__name__
            component_metadata["injected_context_keys"] = cls.get_created_keys()
        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    def collect(self, data: Any) -> None:
        """
        Collect data from the probe.

        Args:
            data (Any): The data to collect.
        """
        self._probed_data.append(data)

    def get_collected_data(self) -> List[Any]:
        """
        Retrieve all collected probe data.

        Returns:
            List[Any]: The list of collected data.
        """
        return self._probed_data

    def clear_collected_data(self) -> None:
        """
        Clear all collected data, useful for reuse in iterative processes.
        """
        self._probed_data.clear()

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve the list of created keys.
        Returns:
            list: An empty list indicating no keys have been created.
        """

        return []

    @override
    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        """
        Execute the probe on a single data item, collecting the result.

        Args:
            payload (Payload): The input payload.

        Returns:
            Payload: The original data and unchanged context.
        """
        data = payload.data
        context = payload.context
        parameters = self._get_processor_parameters(context)
        probe_result = self.processor.process(data, **parameters)
        self.collect(probe_result)
        return Payload(data, context)


class _ContextDataProcessorNode(_PipelineNode):
    """Apply a :class:`DataOperation` or :class:`DataProbe` to a context value."""

    processor_cls: Type[_BaseDataProcessor]
    input_context_keyword: str
    output_context_keyword: str
    processor_kwargs: Dict[str, Any]

    def __init__(
        self,
        processor_cls: Type[_BaseDataProcessor],
        input_context_keyword: str,
        output_context_keyword: str,
        processor_kwargs: Optional[Dict[str, Any]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        super().__init__(logger)
        self.processor_cls = processor_cls
        self.input_context_keyword = input_context_keyword
        self.output_context_keyword = output_context_keyword
        self.processor_kwargs = processor_kwargs or {}

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "ContextDataProcessorNode",
        }

        try:
            if issubclass(cls.processor_cls, DataOperation):
                component_metadata["wraps_component_type"] = "DataOperation"
            elif issubclass(cls.processor_cls, DataProbe):
                component_metadata["wraps_component_type"] = "DataProbe"

            component_metadata["wrapped_component"] = getattr(
                cls.processor_cls,
                "__name__",
                type(cls.processor_cls).__name__,
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor_cls.__doc__ or ""
            )
            component_metadata["required_context_keys"] = [cls.input_context_keyword]
            component_metadata["injected_context_keys"] = cls.get_created_keys()
            if issubclass(cls.processor_cls, DataOperation):
                component_metadata["input_data_type"] = (
                    cls.processor_cls.input_data_type().__name__
                )
                component_metadata["output_data_type"] = (
                    cls.processor_cls.output_data_type().__name__
                )
            else:
                component_metadata["input_data_type"] = (
                    cls.processor_cls.input_data_type().__name__
                )
        except Exception:
            pass

        return component_metadata

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """Return context keys produced by this node."""
        return [cls.output_context_keyword]

    def _process_single_item_with_context(self, payload: Payload) -> Payload:
        data = payload.data
        context = payload.context

        if self.input_context_keyword not in context.keys():
            raise KeyError(self.input_context_keyword)
        context_value = context.get_value(self.input_context_keyword)
        processor = self.processor_cls(**self.processor_kwargs)
        result = processor.process(context_value)
        _ContextObserver.update_context(context, self.output_context_keyword, result)
        return Payload(data, context)

    def _process(self, payload: Payload) -> Payload:
        return self._process_single_item_with_context(payload)


class _ContextProcessorNode(_PipelineNode):
    """
    A node that wraps a context processor.
    """

    processor: ContextProcessor

    def __init__(
        self,
        processor: Type[ContextProcessor],
        processor_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a Node with the specified context processor, and parameters.

        Args:
            processor (Type[ContextProcessor]): The class of the context processor associated with this node.
            processor_config (Optional[Dict]): Operation parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} ({processor.__name__})"
        )
        processor_config = processor_config or {}
        self.processor = processor(logger, **processor_config)
        self.processor_config = processor_config

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        component_metadata: Dict[str, str | List[str]] = {
            "component_type": "ContextProcessorNode",
            "wraps_component_type": "ContextProcessor",
        }

        try:
            component_metadata["wrapped_component"] = getattr(
                cls.processor, "__name__", type(cls.processor).__name__
            )
            component_metadata["wrapped_component_docstring"] = (
                cls.processor.__doc__ or ""
            )
            component_metadata["required_context_keys"] = cls.get_required_keys()
            component_metadata["suppressed_context_keys"] = cls.get_suppressed_keys()
            # The output data type is the same as the input data type for probe nodes
            component_metadata["injected_context_keys"] = cls.get_created_keys()

        except Exception:
            # no binding available at this abstract level
            pass
        return component_metadata

    def __str__(self) -> str:
        """
        Return a string representation of the node.

        Returns:
            str: A string summarizing the node's attributes and execution summary.
        """
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     processor={self.processor},\n"
            f"     processor_config={self.processor_config},\n"
            f"     Execution summary: {self.stop_watch}\n"
            f")"
        )

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or modify during its execution.
        """

        return cls.processor.get_created_keys()

    @classmethod
    def get_required_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys required by the processor.

        Returns:
            List[str]: A list of context keys.
        """
        return cls.processor.get_required_keys()

    @classmethod
    def get_suppressed_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be removed by the processor.

        Returns:
            List[str]: A list of context keys that the processor will remove during its execution.
        """
        return cls.processor.get_suppressed_keys()

    def _process(self, payload: Payload) -> Payload:
        """
        Processes the given data and context.

        Args:
            payload (Payload): The payload to process.

        Returns:
            Payload: The processed data and context.
        """

        data = payload.data
        context = payload.context
        updated_context = self.processor.operate_context(context)

        return Payload(data, updated_context)
