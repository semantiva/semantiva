from typing import Dict, Optional, Type, Tuple
from ...data_types.data_types import BaseDataType
from ...context_processors.context_types import ContextType
from ...data_io import DataSource, PayloadSource, DataSink, PayloadSink
from ...logger import Logger
from ...data_processors.data_io_wrapper_factory import (
    DataIOWrapperFactory,
)
from .nodes import DataNode


# Lets create the new Node classes for Data I/O
class DataSourceNode(DataNode):
    """
    A node that loads data from a data source.

    This node wraps a DataSource to load data and inject it into the pipeline.

    Attributes:
        data_source (DataSource): The data source instance used to load data.
    """

    def __init__(
        self,
        data_io_class: Type[DataSource],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a DataSourceNode with the specified data source.

        Args:
            processor (Type[DataSource]): The data source class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            DataIOWrapperFactory.create_data_operation(data_io_class),
            processor_parameters,
            logger,
        )

    def output_data_type(self):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return self.processor.output_data_type()

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: A list of context keys that the processor will add or create
                       as a result of execution.
        """
        return []

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding single context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding single context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """

        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        output_data = self.processor.process(data, **parameters)

        return output_data, self.observer_context


class PayloadSourceNode(DataNode):
    """
    A node that loads data from a payload source.

    This node wraps a PayloadSource to load data and inject it into the pipeline.

    Attributes:
        payload_source (PayloadSource): The payload source instance used to load data.
    """

    def __init__(
        self,
        data_io_class: Type[PayloadSource],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a PayloadSourceNode with the specified payload source.

        Args:
            processor (Type[PayloadSource]): The payload source class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            DataIOWrapperFactory.create_data_operation(data_io_class),
            processor_parameters,
            logger,
        )

    def output_data_type(self):
        """
        Retrieve the node's output data type.
        """
        return self.processor.output_data_type()

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        return []  # self.processor.get_created_keys()

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding single context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding single context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """

        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        loaded_data, loaded_context = self.processor.process(data, **parameters)

        # Merge context and loaded_context
        for key, value in loaded_context.items():
            if key in context.keys():
                raise KeyError(f"Key '{key}' already exists in the context.")
            context.set_value(key, value)
        return loaded_data, context


class DataSinkNode(DataNode):
    """
    A node that saves data using a data sink.

    This node wraps a DataSink to save data at the end of a pipeline.

    Attributes:
        data_sink (DataSink): The data sink instance used to save data.
    """

    def __init__(
        self,
        data_io_class: Type[DataSink],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a DataSinkNode with the specified data sink.

        Args:
            processor (Type[DataSink]): The data sink class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            DataIOWrapperFactory.create_data_operation(data_io_class),
            processor_parameters,
            logger,
        )

    def input_data_type(self):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return self.processor.input_data_type()

    def output_data_type(self):
        """
        Retrieve the data type that will be produced by the processor.

        Returns:
            Type: The data type that will be produced by the processor.
        """
        return self.processor.output_data_type()

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        return []

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding single context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding single context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """

        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        output_data = self.processor.process(data, **parameters)

        return output_data, self.observer_context


class PayloadSinkNode(DataNode):
    """
    A node that saves data using a payload sink.

    This node wraps a PayloadSink to save data at the end of a pipeline.

    Attributes:
        payload_sink (PayloadSink): The payload sink instance used to save data.
    """

    def __init__(
        self,
        data_io_class: Type[PayloadSink],
        processor_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a PayloadSinkNode with the specified payload sink.

        Args:
            processor (Type[PayloadSink]): The payload sink class for this node.
            processor_parameters (Optional[Dict]): Configuration parameters for the processor. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            DataIOWrapperFactory.create_data_operation(data_io_class),
            processor_parameters,
            logger,
        )

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by the processor.

        Returns:
            List[str]: An empty list indicating that no keys will be created.
        """
        return []

    def output_data_type(self):
        """
        Retrieve this node's output data type. Payload sink nodes act as data passthough.
        """
        return self.input_data_type()

    def _process_single_item_with_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item with its corresponding single context.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding single context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """

        # Save the current context to be used by the processor
        self.observer_context = context
        parameters = self._get_processor_parameters(self.observer_context)
        output_data = self.processor.process(data, **parameters)

        return output_data, self.observer_context
