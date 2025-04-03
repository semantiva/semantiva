from typing import List, Any, Dict, Optional, Type, Tuple
from abc import abstractmethod
from semantiva.context_processors import ContextProcessor
from semantiva.data_processors import (
    BaseDataProcessor,
    DataOperation,
)
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import BaseDataType
from semantiva.logger import Logger
from ..payload_processors import PayloadProcessor


class PipelineNode(PayloadProcessor):
    """
    Represents a node in a processing pipeline that encapsulates a single payload process.

    This class is designed to be a building block in a larger processing pipeline. Each
    instance of this node executes a specific process on the payload.
    """

    processor: BaseDataProcessor | ContextProcessor
    processor_config: Dict
    logger: Logger


class DataNode(PipelineNode):
    """
    Represents a node responsible for processing data within a processing pipeline.

    A DataNode is associated with a processor and acts as the fundamental unit in the pipeline.

    Attributes:
        data_processor (BaseDataProcessor): The data processor associated with the node.
        processor_config (Dict): Configuration parameters for the data processor.
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
        self.processor_config = {} if processor_config is None else processor_config

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
            f"     execution summary: {self.performance_tracker}\n"
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
            f"     Execution summary: {self.performance_tracker}\n"
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

    @classmethod
    def _define_metadata(cls):

        # Define the metadata for the ContextNode
        component_metadata = {
            "component_type": "ContextNode",
        }
        return component_metadata


class ProbeNode(DataNode):
    """
    A specialized DataNode for probing data.
    """

    @classmethod
    def output_data_type(cls):
        """
        Retrieve the node's output data type. The output data type is the same as the input data type for probe nodes.

        Returns:
            Type: The node's output data type.
        """
        return cls.input_data_type()
