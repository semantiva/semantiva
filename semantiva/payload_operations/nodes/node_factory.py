from typing import List, Any, Dict, Optional, Tuple, Type
from semantiva.data_processors.data_io_wrapper_factory import DataIOWrapperFactory
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from semantiva.data_processors import DataOperation, DataProbe
from semantiva.data_types import BaseDataType, NoDataType
from semantiva.component_loader import ComponentLoader
from semantiva.logger import Logger
from .nodes import (
    DataNode,
    ContextNode,
)
from semantiva.context_processors import (
    ContextType,
    ContextCollectionType,
    ContextObserver,
    ContextProcessor,
)
from semantiva.logger import Logger
from .nodes import (
    DataNode,
    ContextNode,
    ProbeNode,
)


class NodeFactory:
    """
    Factory class to create nodes based on the provided configuration.
    """

    @staticmethod
    def create_io_node(
        node_definition: Dict,
        logger: Optional[Logger] = None,
    ) -> DataNode | ContextNode:
        """
        Factory function to create an appropriate data I/O node instance based on the given definition.

        Args:
            node_definition (Dict): A dictionary describing the node configuration.
            logger (Optional[Logger]): Optional logger instance for diagnostic messages.

        Returns:
            DataNode | ContextNode: An instance of a subclass of DataNode or ContextNode.

        Raises:
            ValueError: If the node definition is invalid or if the processor type is unsupported.
        """
        processor = node_definition.get("processor")
        parameters = node_definition.get("parameters", {})

        def get_class(class_name):
            """Helper function to retrieve the class from the loader if the input is a string."""
            if isinstance(class_name, str):
                return ComponentLoader.get_class(class_name)
            return class_name

        # Resolve the processor class if provided as a string.
        processor = get_class(processor)

        if processor is None or not isinstance(processor, type):
            raise ValueError("processor must be a class type or a string, not None.")

        elif issubclass(processor, DataSource):
            return NodeFactory.create_data_source_node(logger, processor, parameters)
        elif issubclass(processor, PayloadSource):
            return NodeFactory.create_payload_source_node(logger, processor, parameters)
        elif issubclass(processor, DataSink):
            return NodeFactory.create_data_sink_node(processor, parameters)
        elif issubclass(processor, PayloadSink):
            return NodeFactory.create_payload_sink_node(processor, parameters)
        else:
            raise ValueError(
                "Unsupported processor. Processor must be of type DataOperation, DataProbe, DataSource, PayloadSource, DataSink, or PayloadSink."
            )

    @staticmethod
    def create_payload_source_node(logger, processor_class, parameters):

        class PayloadSourceNode(DataNode):
            """
            A node that loads data from a payload source.

            This node wraps a PayloadSource to load data and inject it into the pipeline.

            Attributes:
                payload_source (PayloadSource): The payload source instance used to load data.
            """

            processor = DataIOWrapperFactory.create_data_operation(processor_class)

            def __init__(
                self,
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
                    self.processor,
                    processor_parameters,
                    logger,
                )

            @classmethod
            def output_data_type(cls):
                """
                Retrieve the node's output data type.
                """
                return cls.processor.output_data_type()

            @classmethod
            def get_created_keys(cls):
                """
                Retrieve a list of context keys that will be created by the processor.

                Returns:
                    List[str]: An empty list indicating that no keys will be created.
                """
                cls.processor.get_created_keys()

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

            @classmethod
            def _define_metadata(cls):

                # Define the metadata for the PayloadSourceNode
                component_metadata = {
                    "component_type": "PayloadSourceNode",
                    "payload_source": cls.data_io_class.__name__,
                    "input_parameters": cls.data_io_class.get_input_parameters(),
                    "input_data_type": "NoDataType",
                    "output_data_type": cls.output_data_type(),
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return PayloadSourceNode(
            data_io_class=processor,
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_payload_sink_node(processor, parameters):

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

            @classmethod
            def get_created_keys(cls):
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

            @classmethod
            def _define_metadata(cls):

                # Define the metadata for the PayloadSinkNode
                component_metadata = {
                    "component_type": "PayloadSinkNode",
                    "payload_source": cls.data_io_class.__name__,
                    "input_parameters": cls.data_io_class.get_input_parameters(),
                    "input_data_type": cls.input_data_type(),
                    "output_data_type": cls.input_data_type(),  # DataSinkNodes act as data passthrough
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return PayloadSinkNode(
            data_io_class=processor,
            processor_parameters=parameters,
        )

    @staticmethod
    def create_data_sink_node(processor_class, parameters):

        class DataSinkNode(DataNode):
            """
            A node that saves data using a data sink.

            This node wraps a DataSink to save data at the end of a pipeline.

            Attributes:
                data_sink (DataSink): The data sink instance used to save data.
            """

            processor = processor_class

            def __init__(
                self,
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
                    DataIOWrapperFactory.create_data_operation(self.processor),
                    processor_parameters,
                    logger,
                )

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
            def get_created_keys(cls):
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

            @classmethod
            def _define_metadata(cls):
                excluded_parameters = ["self", "data"]
                annotated_parameter_list = [
                    f"{param_name}: {param_type}"
                    for param_name, param_type in cls._retrieve_parameter_signatures(
                        cls.processor._send_data, excluded_parameters
                    )
                ]

                # Define the metadata for the DataSinkNode
                component_metadata = {
                    "component_type": "DataSinkNode",
                    "processor": cls.processor.__name__,
                    "processor_docstring": cls.processor.get_metadata().get(
                        "docstring"
                    ),
                    "input_parameters": annotated_parameter_list or "None",
                    "input_data_type": cls.input_data_type().__name__,
                    "output_data_type": cls.input_data_type().__name__,  # DataSinkNodes act as data passthrough
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return DataSinkNode(
            processor_parameters=parameters,
        )

    @staticmethod
    def create_data_source_node(logger, processor_class, parameters):
        class DataSourceNode(DataNode):
            """
            A node that loads data from a data source.

            This node wraps a DataSource to load data and inject it into the pipeline.

            Attributes:
                data_source (DataSource): The data source instance used to load data.
            """

            processor = processor_class

            def __init__(
                self,
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
                    DataIOWrapperFactory.create_data_operation(self.processor),
                    processor_parameters,
                    logger,
                )

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
            def get_created_keys(cls):
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

            @classmethod
            def _define_metadata(cls):

                # Define the metadata for the DataSourceNode
                component_metadata = {
                    "component_type": "DataSourceNode",
                    "processor": cls.processor.__name__,
                    "processor_docstring": cls.processor.get_metadata().get(
                        "docstring"
                    ),
                    "input_data_type": "NoDataType",
                    "output_data_type": cls.output_data_type().__name__,
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return DataSourceNode(
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_operation_node(logger, processor_class, parameters):

        class OperationNode(DataNode):
            """
            Node that applies an data operation, potentially modifying it.
            It interacts with `ContextObserver` to update the context.
            """

            processor = processor_class

            def __init__(
                self,
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
                super().__init__(self.processor, processor_parameters, logger)

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
            def get_created_keys(cls):
                """
                Retrieve a list of context keys that will be created by the processor.

                Returns:
                    List[str]: A list of context keys that the processor will add or create
                            as a result of execution.
                """
                return cls.processor.get_created_keys()

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

            @classmethod
            def _define_metadata(cls):
                # Define the metadata for the DataOperationNode
                component_metadata = {
                    "component_type": "DataOperationNode",
                    "processor": cls.processor.__name__,
                    "processor_docstring": cls.processor.get_metadata().get(
                        "docstring"
                    ),
                    "input_parameters": cls.processor.get_processing_parameter_names(),
                    "input_data_type": cls.input_data_type().__name__,
                    "output_data_type": cls.output_data_type().__name__,
                    "injected_context_keys": cls.get_created_keys() or "None",
                }

                return component_metadata

        return OperationNode(
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_probe_context_injector(
        logger, processor_class, parameters, context_keyword_
    ):
        if not context_keyword_ or not isinstance(context_keyword_, str):
            raise ValueError("context_keyword must be a non-empty string.")

        class ProbeContextInjectorNode(ProbeNode):
            """
            A node that injects probe results into the execution context.

            This node uses a data probe to extract information from the input data
            and then injects the result into the context under a specified keyword.

            Attributes:
                context_keyword (str): The key under which the probe result is stored in the context.
            """

            processor = processor_class
            context_keyword = context_keyword_

            def __init__(
                self,
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
                super().__init__(self.processor, processor_parameters, logger)

            @classmethod
            def input_data_type(cls):
                """
                Retrieve the expected input data type for the data processor.

                Returns:
                    Type: The expected input data type for the data processor.
                """
                return cls.processor.input_data_type()

            @classmethod
            def output_data_type(cls):
                """
                Retrieve the output data type of the node, which is the same as the input data type for probe nodes.
                """
                return cls.processor.input_data_type()

            @classmethod
            def get_created_keys(cls):
                """
                Retrieve a list of context keys that will be created by the processor.

                Returns:
                    List[str]: A list of context keys that the processor will add or create
                    as a result of execution.
                """
                return [cls.context_keyword]

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
                    f"     execution summary: {self.performance_tracker}\n"
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
                    ContextObserver.update_context(
                        context, self.context_keyword, probe_result
                    )

                return data, context

            @classmethod
            def _define_metadata(cls):

                # Define the metadata for the ProbeContextInjectorNode
                component_metadata = {
                    "component_type": "ProbeContextInjectorNode",
                    "processor": cls.processor.__name__,
                    "processor_docstring": cls.processor.get_metadata().get(
                        "docstring"
                    ),
                    "input_data_type": cls.input_data_type().__name__,
                    "output_data_type": cls.input_data_type().__name__,  # Probe nodes have the same input and output data types
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return ProbeContextInjectorNode(
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_probe_result_collector(logger, processor_, parameters):

        class ProbeResultCollectorNode(ProbeNode):
            """
            A node for collecting probed data.

            Attributes:
                _probed_data (List[Any]): A list of probed data.
            """

            processor = processor_

            def __init__(
                self,
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
                super().__init__(self.processor, processor_parameters, logger)
                self._probed_data: List[Any] = []

            @classmethod
            def input_data_type(cls):
                """
                Retrieve the expected input data type for the data processor.

                Returns:
                    Type: The expected input data type for the data processor.
                """
                return cls.processor.input_data_type()

            @classmethod
            def output_data_type(cls):
                """
                Retrieve the output data type of the node, which is the same as the input data type for probe nodes.
                """
                return cls.processor.input_data_type()

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
            def get_created_keys(cls):
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

            @classmethod
            def _define_metadata(cls):

                # Define the metadata for the ProbeResultCollectorNode
                component_metadata = {
                    "component_type": "ProbeResultCollectorNode",
                    "processor": cls.processor.__name__,
                    "processor_docstring": cls.processor.get_metadata().get(
                        "docstring"
                    ),
                    "input_data_type": cls.input_data_type().__name__,
                    "output_data_type": cls.input_data_type().__name__,  # Probe nodes have the same input and output data types
                    "injected_context_keys": cls.get_created_keys() or "None",
                }
                return component_metadata

        return ProbeResultCollectorNode(
            processor_parameters=parameters,
            logger=logger,
        )


# Main node factory function
def node_factory(
    node_definition: Dict,
    logger: Optional[Logger] = None,
) -> DataNode | ContextNode:
    """
    Factory function to create an appropriate node instance based on the given definition.

    The node definition dictionary should include:
      - "processor": The class (or a string that can be resolved to a class) for the processor.
      - "parameters": (Optional) A dictionary of parameters for the processor.
      - "context_keyword": (Optional) A string specifying the context key for probe injection.

    Args:
        node_definition (Dict): A dictionary describing the node configuration.
        logger (Optional[Logger]): Optional logger instance for diagnostic messages.

    Returns:
        DataNode | ContextNode: An instance of a subclass of DataNode or ContextNode.

    Raises:
        ValueError: If the node definition is invalid or if the processor type is unsupported.
    """

    def get_class(class_name):
        """Helper function to retrieve the class from the loader if the input is a string."""
        if isinstance(class_name, str):
            return ComponentLoader.get_class(class_name)
        return class_name

    processor = node_definition.get("processor")
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    # Resolve the processor class if provided as a string.
    processor = get_class(processor)

    if processor is None or not isinstance(processor, type):
        raise ValueError("processor must be a class type or a string, not None.")

    if issubclass(processor, ContextProcessor):
        return ContextNode(processor, processor_config=parameters, logger=logger)

    elif issubclass(processor, DataOperation):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataOperation nodes."
            )
        return NodeFactory.create_operation_node(logger, processor, parameters)
    elif issubclass(processor, DataProbe):
        if context_keyword is not None:
            return NodeFactory.create_probe_context_injector(
                logger, processor, parameters, context_keyword
            )
        else:
            return NodeFactory.create_probe_result_collector(
                logger, processor, parameters
            )
    elif issubclass(processor, (DataSource, PayloadSource, DataSink, PayloadSink)):
        return NodeFactory.create_io_node(node_definition, logger)
    else:
        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation or DataProbe."
        )
