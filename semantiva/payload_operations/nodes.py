from typing import List, Any, Dict, Optional, Type, Tuple
from .stop_watch import StopWatch
from ..context_operations.context_operations import (
    ContextOperation,
    ContextPassthrough,
)
from ..data_operations.data_operations import (
    BaseDataOperation,
    DataAlgorithm,
    DataProbe,
)
from ..context_operations.context_types import ContextType, ContextCollectionType
from ..data_types.data_types import BaseDataType, DataCollectionType
from ..logger import Logger
from ..component_loader import ComponentLoader
from .payload_operations import PayloadOperation


class Node(PayloadOperation):
    """
    Represents a node in the semantic framework.

    A node is associated with a data operation and acts as a fundamental unit
    in processing pipelines or networks.

    Attributes:
        data_operation (BaseDataOperation): The data operation associated with the node.
        context_operation (ContextOperation): The context operation managing context updates.
        operation_config (Dict): Configuration parameters for the data operation.
        stop_watch (StopWatch): Tracks the execution time of the node's operation.
        logger (Logger): Logger instance for diagnostic messages.
    """

    data_operation: BaseDataOperation
    context_operation: ContextOperation
    operation_config: Dict
    stop_watch: StopWatch
    logger: Logger

    def __init__(
        self,
        data_operation: Type[BaseDataOperation],
        context_operation: Type[ContextOperation],
        operation_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a Node with the specified data operation, context operation, and parameters.

        Args:
            data_operation (Type[BaseDataOperation]): The class of the data operation associated with this node.
            context_operation (Type[ContextOperation]): The class for managing the node's context.
            operation_config (Optional[Dict]): Operation parameters (overrides values extracted from context). Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        self.logger.info(
            f"Initializing {self.__class__.__name__} ({data_operation.__name__})"
        )
        self.data_operation = (
            data_operation(self, logger)
            if issubclass(data_operation, DataAlgorithm)
            else data_operation(logger=logger)
        )
        self.context_operation = context_operation(logger)
        self.stop_watch = StopWatch()
        self.operation_config = {} if operation_config is None else operation_config

    def _get_operation_parameters(self, context: ContextType) -> dict:
        """
        Retrieve the parameters required for the associated data operation.

        Args:
            context (ContextType): Contextual information used to resolve parameter values.

        Returns:
            dict: A dictionary mapping parameter names to their values.
        """
        parameter_names = self.data_operation.get_operation_parameter_names()
        parameters = {}
        for name in parameter_names:
            parameters[name] = self._fetch_parameter_value(name, context)
        return parameters

    def _fetch_parameter_value(self, name: str, context: ContextType) -> Any:
        """
        Fetch a parameter value based on the operation configuration or the context.

        Args:
            name (str): The name of the parameter to fetch.
            context (ContextType): Contextual information for resolving parameter values.

        Returns:
            Any: The value of the parameter, with `operation_config` taking precedence over the context.
        """
        if name in self.operation_config:
            return self.operation_config[name]
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
            f"     data_operation={self.data_operation},\n"
            f"     context_operation={self.context_operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}\n"
            f")"
        )


class AlgorithmNode(Node):
    """
    A specialized node for executing algorithmic operations.

    Attributes:
        data_operation (DataAlgorithm): The data algorithm associated with the node.
    """

    def __init__(
        self,
        data_operation: Type[DataAlgorithm],
        context_operation: Type[ContextOperation],
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize an AlgorithmNode with the specified data algorithm.

        Args:
            data_operation (Type[DataAlgorithm]): The data algorithm for this node.
            context_operation (Type[ContextOperation]): The context operation for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        operation_parameters = (
            {} if operation_parameters is None else operation_parameters
        )
        super().__init__(
            data_operation, context_operation, operation_parameters, logger
        )

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute the data operation for an algorithm node.

        The method processes the input data using the associated data operation and
        updates the context accordingly. It supports both single-instance and collection-based
        processing.

        Args:
            data (BaseDataType): The input data for the operation.
            context (ContextType): The context required for execution.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple with:
                - The processed output data.
                - The updated context.
        """
        result_data, result_context = data, context
        input_type = self.data_operation.input_data_type()

        if type(result_data) == input_type:
            result_data, result_context = self._process_node_call(
                result_data, result_context
            )
        elif (
            isinstance(result_data, DataCollectionType)
            and input_type == result_data.collection_base_type()
        ):
            result_data, result_context = self._slicing_strategy(
                result_data, result_context
            )
        else:
            raise TypeError(
                f"Incompatible data type for Node {self.data_operation.__class__.__name__} "
                f"expected {input_type}, but received {type(result_data)}."
            )
        return result_data, result_context

    def _process_node_call(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Process a single data item using the associated data operation.

        This method updates the context using the context operation and retrieves the operation
        parameters before invoking the data operation.

        Args:
            data (BaseDataType): A single data item.
            context (ContextType): The context associated with the data item.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing the output data and the updated context.
        """
        self.stop_watch.start()
        self.observer_context = self.context_operation.operate_context(context)
        parameters = self._get_operation_parameters(self.observer_context)
        output_data = self.data_operation.process(data, **parameters)
        self.stop_watch.stop()
        return output_data, self.observer_context

    def _slicing_strategy(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a collection of data items element-wise, applying slicing if necessary.

        If the context is a ContextCollectionType, data items and their corresponding context
        elements are processed in parallel. If the context is a single ContextType, it is reused
        for each data item.

        Args:
            data_collection (DataCollectionType): The collection of data items to process.
            context (ContextType): The context or collection of contexts for processing.

        Returns:
            Tuple[BaseDataType, ContextType]:
                - A new DataCollectionType with the processed data items.
                - Either a new ContextCollectionType (if parallel slicing was applied) or the updated ContextType.

        Raises:
            ValueError: If the data collection and context collection lengths do not match.
        """
        processed_data_collection = type(data_collection)()
        if isinstance(context, ContextCollectionType):
            if len(data_collection) != len(context):
                raise ValueError(
                    "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
                )
            processed_context_collection = ContextCollectionType()
            for d_item, c_item in zip(data_collection, context):
                out_data, out_context = self._process_node_call(d_item, c_item)
                processed_data_collection.append(out_data)
                processed_context_collection.append(out_context)
            return processed_data_collection, processed_context_collection
        else:
            current_context = context
            self.logger.warning(
                "Context operations in this slicing mode are lost because the context is reused "
                "for each data item instead of being processed in parallel with the data collection."
            )
            for d_item in data_collection:
                out_data, current_context = self._process_node_call(
                    d_item, current_context
                )
                processed_data_collection.append(out_data)
            return processed_data_collection, current_context


class ProbeNode(Node):
    """
    A specialized node for probing data within the framework.

    This class can be extended to add common functionalities for probe nodes.
    """

    pass


class ProbeContextInjectorNode(ProbeNode):
    """
    A node for injecting probe results into data context.

    This node uses a data probe to extract information from the input data and injects
    the probe result into the context under a specified keyword.

    Attributes:
        data_operation (DataProbe): The data probe associated with this node.
        context_operation (ContextOperation): The context operation managing context updates.
        context_keyword (str): The key under which the probe result is injected into the context.
        operation_config (Optional[Dict]): Configuration parameters for the operation.
    """

    def __init__(
        self,
        data_operation: Type[BaseDataOperation],
        context_operation: Type[ContextOperation],
        context_keyword: str,
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeContextInjectorNode with the specified data operation and context keyword.

        Args:
            data_operation (Type[BaseDataOperation]): The data probe class for this node.
            context_operation (Type[ContextOperation]): The context operation class for this node.
            context_keyword (str): The keyword used to inject the probe result into the context.
            operation_parameters (Optional[Dict]): Operation configuration parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.

        Raises:
            ValueError: If `context_keyword` is not provided or is not a non-empty string.
        """
        super().__init__(
            data_operation, context_operation, operation_parameters, logger
        )
        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")
        self.context_keyword = context_keyword

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process the input data by performing the probe operation and injecting its result into the context.

        This method handles both single data items and collections. When the input data is a collection,
        the method applies slicing:
          - If the context is a ContextCollectionType, each data item is processed with its corresponding context.
          - If the context is a single ContextType, the probe results for all data items are accumulated
            into a list and injected under the specified context keyword.

        Args:
            data (BaseDataType): The input data or collection of data items.
            context (ContextType): The context or context collection for processing.

        Returns:
            Tuple[BaseDataType, ContextType]: A tuple containing the (possibly unchanged) input data
            and the updated context with the probe results injected.

        Raises:
            TypeError: If the input data type is incompatible with the node's expected type.
        """
        expected_input_type = self.data_operation.input_data_type()

        # Case A: Single data item processing
        if type(data) == expected_input_type:
            self.stop_watch.start()
            updated_context = self.context_operation.operate_context(context)
            parameters = self._get_operation_parameters(updated_context)
            probe_result = self.data_operation.process(data, **parameters)
            updated_context.set_value(self.context_keyword, probe_result)
            self.stop_watch.stop()
            return data, updated_context

        # Case B: Collection processing
        elif (
            isinstance(data, DataCollectionType)
            and expected_input_type == data.collection_base_type()
        ):
            processed_data_collection = type(data)()
            if isinstance(context, ContextCollectionType):
                if len(data) != len(context):
                    raise ValueError(
                        "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
                    )
                processed_context_collection = ContextCollectionType()
                for d_item, c_item in zip(data, context):
                    out_data, out_context = self._process(d_item, c_item)
                    processed_data_collection.append(out_data)
                    processed_context_collection.append(out_context)
                return processed_data_collection, processed_context_collection
            else:
                # Single context: Accumulate probe results in a list
                probed_results: List[Any] = []
                for d_item in data:
                    out_data, updated_context = self._process(d_item, context)
                    processed_data_collection.append(out_data)
                    # Extract the probe result injected into the updated context.
                    probe_result = updated_context.get_value(self.context_keyword)
                    probed_results.append(probe_result)
                # Inject the full list of probe results into the context.
                context.set_value(self.context_keyword, probed_results)
                return processed_data_collection, updated_context

        else:
            raise TypeError(
                f"Incompatible data type for {self.__class__.__name__}: expected {expected_input_type} "
                f"or a collection of its base type, but received {type(data)}."
            )

    def __str__(self) -> str:
        """
        Return a string representation of the ProbeContextInjectorNode.

        Returns:
            str: A string summarizing the node's attributes and execution summary.
        """
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     data_operation={self.data_operation},\n"
            f"     context_keyword={self.context_keyword},\n"
            f"     context_operation={self.context_operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}\n"
            f")"
        )


class ProbeResultCollectorNode(ProbeNode):
    """
    A node for collecting probed data during operations.

    Attributes:
        _probed_data (List[Any]): A list of data collected during probing operations.
    """

    def __init__(
        self,
        data_operation: Type[DataProbe],
        context_operation: Type[ContextOperation],
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeResultCollectorNode with the specified data probe.

        Args:
            data_operation (Type[DataProbe]): The data probe class for this node.
            context_operation (Type[ContextOperation]): The context operation class for this node.
            operation_parameters (Optional[Dict]): Configuration parameters for the operation. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(
            data_operation, context_operation, operation_parameters, logger
        )
        self._probed_data: List[Any] = []

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Execute the data probe operation and collect its result.

        This method processes a single data item, updates the context using the context operation,
        and collects the probe result for later retrieval. If the input is a collection,
        it delegates to _slicing_strategy.

        Args:
            data (BaseDataType): The input data to be probed.
            context (ContextType): Contextual information required for execution.

        Returns:
            Tuple[BaseDataType, ContextType]: A tuple containing the (unchanged) input data and the updated context.
        """
        self.stop_watch.start()
        expected_input_type = self.data_operation.input_data_type()

        if type(data) == expected_input_type:
            _, updated_context = self._process_node_call(data, context)
        elif (
            isinstance(data, DataCollectionType)
            and expected_input_type == data.collection_base_type()
        ):
            _, updated_context = self._slicing_strategy(data, context)
        else:
            raise TypeError(
                f"Incompatible data type for {self.__class__.__name__}: expected {expected_input_type} "
                f"or a collection of its base type, but received {type(data)}."
            )
        self.stop_watch.stop()
        return data, updated_context

    def _process_node_call(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a single data item using the associated data probe.

        This method updates the context using the context operation, retrieves the operation
        parameters, and performs the probe operation. The probe result is collected via the
        collect() method.

        Args:
            data (BaseDataType): A single data item.
            context (ContextType): The context associated with the data item.

        Returns:
            Tuple[BaseDataType, ContextType]: A tuple containing the (unchanged) data and the updated context.
        """
        updated_context = self.context_operation.operate_context(context)
        parameters = self._get_operation_parameters(updated_context)
        probe_result = self.data_operation.process(data, **parameters)
        self.collect(probe_result)
        return data, updated_context

    def _slicing_strategy(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a collection of data items element-wise, applying slicing if necessary.

        For parallel processing (when context is a ContextCollectionType), each (data, context)
        pair is processed independently. For single-context processing, the probe results for all
        items are collected into a list and stored in the context under the probe's class name.

        Args:
            data_collection (DataCollectionType): The collection of data items to process.
            context (ContextType): The context or collection of contexts for processing.

        Returns:
            Tuple[BaseDataType, ContextType]:
                - The (unchanged) data collection.
                - The updated context, which in the single-context case contains a list of all probe results.

        Raises:
            ValueError: If the data collection and context collection lengths do not match.
        """
        probed_results: List[Any] = []
        processed_data_collection = type(data_collection)()
        # Parallel slicing
        if isinstance(context, ContextCollectionType):
            if len(data_collection) != len(context):
                raise ValueError(
                    "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
                )
            processed_context_collection = ContextCollectionType()
            for d_item, c_item in zip(data_collection, context):
                updated_context = self.context_operation.operate_context(c_item)
                parameters = self._get_operation_parameters(updated_context)
                probe_result = self.data_operation.process(d_item, **parameters)
                probed_results.append(probe_result)
                processed_data_collection.append(d_item)
                processed_context_collection.append(updated_context)
            # Optionally, one might inject the list of all probe results into each context item;
            # here we simply return the collection of updated contexts.
            self.collect(probed_results)
            return data_collection, processed_context_collection
        else:
            # Single context: process each item once and accumulate the probe results.
            updated_context = self.context_operation.operate_context(context)
            parameters = self._get_operation_parameters(updated_context)
            for d_item in data_collection:
                probe_result = self.data_operation.process(d_item, **parameters)
                probed_results.append(probe_result)
                processed_data_collection.append(d_item)
            # Store the aggregated probe results in the single context.
            self.collect(probed_results)
            return data_collection, context

    def collect(self, data: Any) -> None:
        """
        Collect data from the probe operation.

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


def node_factory(
    node_definition: Dict,
    component_loader: ComponentLoader,
    logger: Optional[Logger] = None,
) -> Node:
    """
    Factory function to create a Node instance based on the provided definition.

    The node definition dictionary is expected to contain:
      - "operation": A class for a DataOperation (required).
      - "context_operation": A class for a ContextOperation (optional, defaults to ContextPassthrough).
      - "parameters": A dictionary of operation parameters (optional).
      - "context_keyword": A string for context injection (optional).

    Args:
        node_definition (Dict): A dictionary defining the node structure.
        logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.

    Returns:
        Node: An instance of the appropriate Node subclass.

    Raises:
        ValueError: If the node definition is invalid or the operation type is unsupported.
    """

    def get_class_if_needed(class_name, component_loader):
        """Helper function to retrieve the class from the loader if the input is a string."""
        if isinstance(class_name, str):
            return component_loader.get_class(class_name)
        return class_name

    operation = node_definition.get("operation")
    context_operation = node_definition.get("context_operation", ContextPassthrough)
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    # Use the helper function to get the correct class for both operation and context_operation
    operation = get_class_if_needed(operation, component_loader)
    context_operation = get_class_if_needed(context_operation, component_loader)

    if operation is None or not isinstance(operation, type):
        raise ValueError("operation must be a class type or a string, not None.")

    if issubclass(operation, DataAlgorithm):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataAlgorithm nodes."
            )
        return AlgorithmNode(
            data_operation=operation,
            context_operation=context_operation,
            operation_parameters=parameters,
            logger=logger,
        )
    elif issubclass(operation, DataProbe):
        if context_keyword is not None:
            return ProbeContextInjectorNode(
                data_operation=operation,
                context_operation=context_operation,
                context_keyword=context_keyword,
                operation_parameters=parameters,
                logger=logger,
            )
        else:
            return ProbeResultCollectorNode(
                data_operation=operation,
                context_operation=context_operation,
                operation_parameters=parameters,
                logger=logger,
            )
    else:
        raise ValueError(
            "Unsupported operation type. Operation must be of type DataAlgorithm or DataProbe."
        )
