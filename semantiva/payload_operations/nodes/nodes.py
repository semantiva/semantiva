from typing import List, Any, Dict, Optional, Type, Tuple
from abc import abstractmethod
from ..stop_watch import StopWatch
from ...context_processors.context_processors import ContextProcessor
from ...data_processors.data_processors import (
    BaseDataProcessor,
    DataOperation,
    DataProbe,
)
from ...context_processors.context_types import ContextType, ContextCollectionType
from ...data_types.data_types import BaseDataType, DataCollectionType
from ...logger import Logger
from ..payload_processors import PayloadProcessor
from semantiva.context_processors.context_observer import ContextObserver


class PipelineNode(PayloadProcessor):
    """
    Represents a node in a processing pipeline that encapsulates a single payload process.

    This class is designed to be a building block in a larger processing pipeline. Each
    instance of this node executes a specific process on the payload.
    """

    processor: BaseDataProcessor | ContextProcessor
    processor_config: Dict
    stop_watch: StopWatch
    logger: Logger


class DataNode(PipelineNode):
    """
    Represents a node responsible for processing data within a processing pipeline.

    A DataNode is associated with a processor and acts as the fundamental unit in the pipeline.

    Attributes:
        data_processor (BaseDataProcessor): The data processor associated with the node.
        processor_config (Dict): Configuration parameters for the data processor.
        stop_watch (StopWatch): Tracks the execution time of the node's processing.
        logger (Logger): Logger instance for diagnostic messages.
    """

    processor: BaseDataProcessor

    def __init__(
        self,
        processor: Type[BaseDataProcessor],
        processor_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a DataNode with a specific data processor and its configuration.

        Args:
            processor (Type[BaseDataProcessor]): The class of the data processor associated with this node.
            processor_config (Optional[Dict]): Configuration parameters for the data processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        print("processor", processor)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} ({processor.__name__})"
        )
        self.processor = (
            processor(self, self.logger)
            if issubclass(processor, DataOperation)
            else processor(logger=self.logger)
        )
        self.stop_watch = StopWatch()
        self.processor_config = {} if processor_config is None else processor_config

    def input_data_type(self):
        """
        Retrieve the expected input data type for the data processor.

        Returns:
            Type: The expected input data type for the data processor.
        """
        return self.processor.input_data_type()

    @abstractmethod
    def output_data_type(self):
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
        assert (
            name in context.keys()
        ), f"Unable to resolve parameter '{name}' from context or node configuration."
        return context.get_value(name)

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

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys created or updated by the data processor.

        Returns:
            List[str]: A list of context keys that the data processor crestes or modifies
                       as a result of execution.
        """

    @abstractmethod
    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding context.

        Args:
            data (BaseDataType): A data instance.
            context (ContextType): The corresponding context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Process payload.

        This method processes the given payload using the configured data processor and updates the execution context.
        It supports both single payload objects and collections of payloads by applying the appropriate processing strategy
        based on the input types.

        Parameters:
            payload (BaseDataType): The payload to be processed.
            execution_context (ContextType): The context at this step, which may be a singular context or a collection of contexts.

        Returns:
            tuple[BaseDataType, ContextType]:
            A tuple where the first element is the processed payload and the second element is the updated execution context.

        Raises:
            ValueError:
            If a single payload is paired with a collection context.
            TypeError:
            If the payload type is incompatible with the expected input type for the data processor.
        """

        result_data, result_context = data, context
        input_type = self.processor.input_data_type()

        if issubclass(type(result_data), input_type):
            return self._process_single_item_with_context(result_data, result_context)
        else:
            raise TypeError(
                f"Incompatible data type for Node {self.processor.__class__.__name__} "
                f"expected {input_type}, but received {type(result_data)}."
            )


class ContextNode(PipelineNode):
    """
    Represents a node in the semantic framework.

    A ContextNode is associated with a context processor and acts as a fundamental unit
    in processing pipelines or networks.

    Attributes:
        processor (ContextProcessor): The context processor associated with the node.
        processor_config (Dict): Configuration parameters for the context processor.
        stop_watch (StopWatch): Tracks the execution time of the node's processor.
        logger (Logger): Logger instance for diagnostic messages.
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
        self.processor = (
            processor(logger, **processor_config)
            if issubclass(processor, (DataOperation, ContextProcessor))
            else processor(logger=logger)
        )
        self.processor_config = processor_config
        self.stop_watch = StopWatch()

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

    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
                       as a result of execution.
        """
        return self.processor.get_created_keys()

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Processes the given data and context.

        Args:
            data (BaseDataType): The data to be processed.
            context (ContextType): The context in which the data is processed.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing the processed data and context.
        """

        updated_context = self.processor.operate_context(context)

        return data, updated_context


class OperationNode(DataNode):
    """
    Node that applies an data operation, potentially modifying it.

    Handles slicing rules to ensure correct association of data with context.
    It interacts with `ContextObserver` to update the context.
    """

    def __init__(
        self,
        processor: Type[DataOperation],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize an OperationNode with the specified data algorithm.

        Args:
            processor (Type[DataOperation]): The data algorithm for this node.
            processor_parameters (Optional[Dict]): Initial configuration for processor parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        processor_parameters = (
            {} if processor_parameters is None else processor_parameters
        )
        super().__init__(processor, processor_parameters, logger)

    def output_data_type(self):
        """
        Retrieve the node's output data type. The request is delegated to the node's data processor.

        Returns:
            Type: The node output data type.
        """
        return self.processor.output_data_type()

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
                       as a result of execution.
        """
        return self.processor.get_created_keys()

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding single context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and the updated context.
        """

        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        output_data = self.processor.process(data, **parameters)

        return output_data, self.observer_context


class ProbeNode(DataNode):
    """
    A specialized DataNode for probing data.
    """

    def output_data_type(self):
        """
        Retrieve the node's output data type. The output data type is the same as the input data type for probe nodes.

        Returns:
            Type: The node's output data type.
        """
        return self.input_data_type()


class ProbeContextInjectorNode(ProbeNode):
    """
    A node that injects probe results into the execution context.

    This node uses a data probe to extract information from the input data
    and then injects the result into the context under a specified keyword.

    Attributes:
        context_keyword (str): The key under which the probe result is stored in the context.
    """

    def __init__(
        self,
        processor: Type[BaseDataProcessor],
        context_keyword: str,
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeContextInjectorNode with the specified data processor and context keyword.

        Args:
            processor (Type[BaseDataProcessor]): The data probe class for this node.
            context_keyword (str): The keyword used to inject the probe result into the context.
            processor_parameters (Optional[Dict]): Operation configuration parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.

        Raises:
            ValueError: If `context_keyword` is not provided or is not a non-empty string.
        """
        super().__init__(processor, processor_parameters, logger)
        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")
        self.context_keyword = context_keyword

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
            as a result of execution.
        """
        return [self.context_keyword]

    def __str__(self) -> str:
        """
        Return a string representation of the ProbeContextInjectorNode.

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

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item and inject the probe result into the context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The context to be updated.

        Returns:
            Tuple[BaseDataType, ContextType]: The unchanged data and the updated context with the probe result.
        """

        parameters = self._get_processor_parameters(context)
        probe_result = self.processor.process(data, **parameters)
        if isinstance(context, ContextCollectionType):
            for index, p_item in enumerate(probe_result):
                ContextObserver.update_context(
                    context, self.context_keyword, p_item, index=index
                )
        else:
            ContextObserver.update_context(context, self.context_keyword, probe_result)

        return data, context


class ProbeResultCollectorNode(ProbeNode):
    """
    A node for collecting probed data.

    Attributes:
        _probed_data (List[Any]): A list of probed data.
    """

    def __init__(
        self,
        processor: Type[DataProbe],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeResultCollectorNode with the specified data probe.

        Args:
            processor (Type[DataProbe]): The data probe class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(processor, processor_parameters, logger)
        self._probed_data: List[Any] = []

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

    def get_created_keys(self):
        """
        Retrieve the list of created keys.
        Returns:
            list: An empty list indicating no keys have been created.
        """

        return []

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Execute the probe on a single data item, collecting the result.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The context, unchanged by this node.

        Returns:
            Tuple[BaseDataType, ContextType]: The original data and unchanged context.
        """
        parameters = self._get_processor_parameters(context)
        probe_result = self.processor.process(data, **parameters)
        self.collect(probe_result)
        return data, context
