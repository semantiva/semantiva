from typing import List, Any, Dict, Optional, Type, Tuple
from abc import abstractmethod
from .stop_watch import StopWatch
from ..context_operations.context_operations import ContextOperation
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


class PipelineNode(PayloadOperation):
    """
    Represents a node in a processing pipeline that encapsulates a single payload operation.

    This class is designed to be a building block in a larger processing pipeline. Each
    instance of this node may perform a specific operation on the payload data, contributing
    to the overall transformation or analysis process.
    """

    operation: BaseDataOperation | ContextOperation
    operation_config: Dict
    stop_watch: StopWatch
    logger: Logger


class DataNode(PipelineNode):
    """
    Represents a node responsible for executing data operations within a processing pipeline.

    A node is associated with a data operation and acts as a fundamental unit
    in processing pipelines or networks.

    Attributes:
        data_operation (BaseDataOperation): The data operation associated with the node.
        operation_config (Dict): Configuration parameters for the data operation.
        stop_watch (StopWatch): Tracks the execution time of the node's operation.
        logger (Logger): Logger instance for diagnostic messages.
    """

    operation: BaseDataOperation

    def __init__(
        self,
        data_operation: Type[BaseDataOperation],
        operation_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a DataNode with a specific data operation and configuration.

        Args:
            data_operation (Type[BaseDataOperation]): The class of the data operation associated with this node.
            operation_config (Optional[Dict]): Operation parameters (overrides values extracted from context). Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} ({data_operation.__name__})"
        )
        self.operation = (
            data_operation(self, self.logger)
            if issubclass(data_operation, DataAlgorithm)
            else data_operation(logger=self.logger)
        )
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
        parameter_names = self.operation.get_operation_parameter_names()
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
            f"     operation={self.operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}\n"
            f")"
        )

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute a data operation for an algorithm node.

        This method processes the input data using the associated data algorithm and updates the context.
        It handles both single data objects and collections of data, applying the appropriate processing strategy
        based on the input types.

        Parameters:
            data (BaseDataType): The input data to be processed.
            context (ContextType): The context for execution, which may be a singular context or a collection of contexts.

            tuple[BaseDataType, ContextType]:
                A tuple where the first element is the processed data and the second element is the updated context.

        Raises:
            ValueError: If a single data object is paired with a collection context.
            TypeError: If the data type is incompatible with the expected input type for the operation.
        """

        result_data, result_context = data, context
        input_type = self.operation.input_data_type()

        if issubclass(type(result_data), input_type):
            return self._execute_single_data_single_context(result_data, result_context)
        elif (
            isinstance(result_data, DataCollectionType)
            and input_type == result_data.collection_base_type()
        ):
            return self._slicing_strategy(result_data, result_context)
        elif not isinstance(result_data, DataCollectionType) and isinstance(
            context, ContextCollectionType
        ):
            return self._execute_single_data_context_collection(result_data, context)
        else:
            raise TypeError(
                f"Incompatible data type for Node {self.operation.__class__.__name__} "
                f"expected {input_type}, but received {type(result_data)}."
            )

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
        if isinstance(context, ContextCollectionType):
            return self._execute_data_collection_context_collection(
                data_collection, context
            )

        else:
            return self._execute_data_collection_single_context(
                data_collection, context
            )

    @abstractmethod
    def _execute_single_data_single_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Process a **single data item** with a **single context**.

        No slicing is required since both data and context are individual objects.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The corresponding single context.

        Returns:
            Tuple[BaseDataType, ContextType]: The processed data and updated context.
        """
        pass

    def _execute_single_data_context_collection(
        self, data: BaseDataType, context: ContextCollectionType
    ) -> Tuple[BaseDataType, ContextCollectionType]:
        """
        Process a **single data item** with a **collection of contexts**.

        This case is invalid since a single data object **cannot** be paired with multiple
        independent contexts. An exception should be raised.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextCollectionType): A collection of contexts.

        Raises:
            ValueError: If this invalid case is encountered.

        Returns:
            Never returns since an exception is raised.
        """
        raise ValueError("Single data object cannot be paired with multiple contexts.")

    @abstractmethod
    def _execute_data_collection_single_context(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[DataCollectionType, ContextType]:
        """
        Process a **collection of data items** using a **single context**.

        Each data slice is processed using the **same** context. Any new context elements
        created during processing must be **stored as a list** under the context keyword.

        Args:
            data (DataCollectionType): A collection of data instances.
            context (ContextType): A single context instance.

        Returns:
            Tuple[DataCollectionType, ContextType]: The processed data collection and updated context.
        """
        pass

    @abstractmethod
    def _execute_data_collection_context_collection(
        self, data_collection: DataCollectionType, context: ContextCollectionType
    ) -> Tuple[DataCollectionType, ContextCollectionType]:
        """
        Process a **collection of data items** using a **collection of contexts**.

        This case requires a **one-to-one mapping** between data slices and context slices.
        Each data item is paired with its respective context element.

        Args:
            data (DataCollectionType): A collection of data instances.
            context (ContextCollectionType): A collection of contexts of equal size.

        Raises:
            ValueError: If the number of data elements and context elements do not match.

        Returns:
            Tuple[DataCollectionType, ContextCollectionType]: The processed data collection and corresponding context collection.
        """
        pass


class ContextNode(PipelineNode):
    """
    Represents a node in the semantic framework.

    A ContextNode is associated with a context operation and acts as a fundamental unit
    in processing pipelines or networks.

    Attributes:
        context_operation (ContextOperation): The context operation associated with the node.
        operation_config (Dict): Configuration parameters for the context operation.
        stop_watch (StopWatch): Tracks the execution time of the node's operation.
        logger (Logger): Logger instance for diagnostic messages.
    """

    operation: ContextOperation

    def __init__(
        self,
        context_operation: Type[ContextOperation],
        operation_config: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a Node with the specified context operation, and parameters.

        Args:
            context_operation (Type[ContextOperation]): The class of the context operation associated with this node.
            operation_config (Optional[Dict]): Operation parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(logger)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} ({context_operation.__name__})"
        )
        operation_config = operation_config or {}
        self.operation = (
            context_operation(logger, **operation_config)
            if issubclass(context_operation, (DataAlgorithm, ContextOperation))
            else context_operation(logger=logger)
        )
        self.operation_config = operation_config
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
            f"     operation={self.operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}\n"
            f")"
        )

    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """
        return self.operation.get_created_keys()

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
        return data, self.operation.operate_context(context)


class AlgorithmNode(DataNode):
    """
    Node that executes an algorithm on data.

    Handles slicing rules to ensure correct association of data with context.
    It interacts with `ContextObserver` to update and track contextual information.
    """

    def __init__(
        self,
        data_operation: Type[DataAlgorithm],
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize an AlgorithmNode with the specified data algorithm.

        Args:
            data_operation (Type[DataAlgorithm]): The data algorithm for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        operation_parameters = (
            {} if operation_parameters is None else operation_parameters
        )
        super().__init__(data_operation, operation_parameters, logger)

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """
        return self.operation.get_created_keys()

    def _execute_single_data_single_context(
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
        self.stop_watch.start()
        # Save the current context to be used by the operation
        self.observer_context = context
        parameters = self._get_operation_parameters(self.observer_context)
        output_data = self.operation.process(data, **parameters)
        self.stop_watch.stop()
        return output_data, self.observer_context

    def _execute_data_collection_single_context(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[DataCollectionType, ContextType]:
        """
        Process a collection of data items using a single context.

        Each item is processed sequentially and the context is updated accordingly.
        For any keys created by the operation, their values are aggregated into lists.

        Args:
            data_collection (DataCollectionType): A collection of data instances.
            context (ContextType): A single context instance used for all items.

        Returns:
            Tuple[DataCollectionType, ContextType]: The processed data collection and updated context.
        """
        processed_data_collection = type(data_collection)()
        current_context = context
        for d_item in data_collection:
            out_data, current_context = self._execute_single_data_single_context(
                d_item, current_context
            )
            processed_data_collection.append(out_data)
            for key in self.get_created_keys():
                new_value = current_context.get_value(key)
                if new_value is None:
                    raise ValueError(
                        f"Missing context element for key '{key}' after processing node call."
                    )
                # Initialize aggregation list if needed and append the new value
                if not isinstance(current_context.get_value(key), list):
                    aggregation = current_context.get_value(key)
                    aggregation = [] if aggregation is None else [aggregation]
                    current_context.set_value(key, aggregation)
                aggregated = current_context.get_value(key)
                aggregated.append(new_value)
                current_context.set_value(key, aggregated)

        return processed_data_collection, current_context

    def _execute_data_collection_context_collection(
        self, data_collection: DataCollectionType, context: ContextCollectionType
    ) -> Tuple[DataCollectionType, ContextCollectionType]:
        """
        Process a collection of data items with a corresponding collection of contexts.

        The data and context collections must be of the same length. Each data item is paired
        with its corresponding context and processed accordingly.

        Args:
            data_collection (DataCollectionType): A collection of data items.
            context (ContextCollectionType): A collection of contexts.

        Returns:
            Tuple[DataCollectionType, ContextCollectionType]: The processed data collection and updated contexts.

        Raises:
            ValueError: If the lengths of data_collection and context do not match.
        """
        processed_data_collection = type(data_collection)()
        if len(data_collection) != len(context):
            raise ValueError(
                "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
            )
        processed_context_collection = ContextCollectionType()
        for d_item, c_item in zip(data_collection, context):
            out_data, out_context = self._execute_single_data_single_context(
                d_item, c_item
            )
            processed_data_collection.append(out_data)
            processed_context_collection.append(out_context)
        return processed_data_collection, processed_context_collection


class ProbeNode(DataNode):
    """
    A specialized DataNode for probing data within the processing framework.

    This base class is intended to be extended to add common functionalities
    for nodes that perform data probing operations.
    """

    pass


class ProbeContextInjectorNode(ProbeNode):
    """
    A node that injects probe results into the execution context.

    This node uses a data probe operation to extract information from the input data
    and then injects the result into the context under a specified keyword.

    Attributes:
        context_keyword (str): The key under which the probe result is stored in the context.
    """

    def __init__(
        self,
        data_operation: Type[BaseDataOperation],
        context_keyword: str,
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeContextInjectorNode with the specified data operation and context keyword.

        Args:
            data_operation (Type[BaseDataOperation]): The data probe class for this node.
            context_keyword (str): The keyword used to inject the probe result into the context.
            operation_parameters (Optional[Dict]): Operation configuration parameters. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.

        Raises:
            ValueError: If `context_keyword` is not provided or is not a non-empty string.
        """
        super().__init__(data_operation, operation_parameters, logger)
        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")
        self.context_keyword = context_keyword

    def get_created_keys(self):
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
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
            f"     data_operation={self.operation},\n"
            f"     context_keyword={self.context_keyword},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}\n"
            f")"
        )

    def _execute_single_data_single_context(
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
        self.stop_watch.start()
        parameters = self._get_operation_parameters(context)
        probe_result = self.operation.process(data, **parameters)
        context.set_value(self.context_keyword, probe_result)
        self.stop_watch.stop()
        return data, context

    def _execute_data_collection_single_context(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[DataCollectionType, ContextType]:
        """
        Process a collection of data items with a single context by applying the probe operation.

        The probe results for each item are aggregated into a list and injected into the context.

        Args:
            data_collection (DataCollectionType): A collection of data items.
            context (ContextType): The shared context for all data items.

        Returns:
            Tuple[DataCollectionType, ContextType]: The processed data collection and updated context.
        """
        processed_data_collection = type(data_collection)()
        probed_results: List[Any] = []
        for d_item in data_collection:
            out_data, context = self._process(d_item, context)
            processed_data_collection.append(out_data)
            # Retrieve the injected probe result for the current item.
            probe_result = context.get_value(self.context_keyword)
            probed_results.append(probe_result)
        # Inject the aggregated list of probe results into the context.
        context.set_value(self.context_keyword, probed_results)
        return processed_data_collection, context

    def _execute_data_collection_context_collection(
        self, data_collection: DataCollectionType, context: ContextCollectionType
    ) -> Tuple[DataCollectionType, ContextCollectionType]:
        """
        Process a collection of data items with a one-to-one mapping to a collection of contexts.

        For each pair, the probe operation is executed and the result is injected into the context.
        Both the processed data collection and the updated context collection are returned.

        Args:
            data_collection (DataCollectionType): A collection of data items.
            context (ContextCollectionType): A collection of contexts.

        Returns:
            Tuple[DataCollectionType, ContextCollectionType]: The processed data collection and updated context collection.

        Raises:
            ValueError: If the lengths of data_collection and context do not match.
        """
        processed_data_collection = type(data_collection)()
        if len(data_collection) != len(context):
            raise ValueError(
                "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
            )
        processed_context_collection = ContextCollectionType()
        for d_item, c_item in zip(data_collection, context):
            out_data, out_context = self._process(d_item, c_item)
            processed_data_collection.append(out_data)
            processed_context_collection.append(out_context)
        return processed_data_collection, processed_context_collection


class ProbeResultCollectorNode(ProbeNode):
    """
    A node for collecting probed data during operations.

    Attributes:
        _probed_data (List[Any]): A list of data collected during probing operations.
    """

    def __init__(
        self,
        data_operation: Type[DataProbe],
        operation_parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize a ProbeResultCollectorNode with the specified data probe.

        Args:
            data_operation (Type[DataProbe]): The data probe class for this node.
            operation_parameters (Optional[Dict]): Configuration parameters for the operation. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        """
        super().__init__(data_operation, operation_parameters, logger)
        self._probed_data: List[Any] = []

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

    def get_created_keys(self):
        """
        Retrieve the list of created keys.
        Returns:
            list: An empty list indicating no keys have been created.
        """

        return []

    def _execute_single_data_single_context(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Execute the probe operation on a single data item, collecting the result.

        Args:
            data (BaseDataType): A single data instance.
            context (ContextType): The context, unchanged by this node.

        Returns:
            Tuple[BaseDataType, ContextType]: The original data and unchanged context.
        """
        parameters = self._get_operation_parameters(context)
        probe_result = self.operation.process(data, **parameters)
        self.collect(probe_result)
        return data, context

    def _execute_data_collection_single_context(
        self, data_collection: DataCollectionType, context: ContextType
    ) -> Tuple[DataCollectionType, ContextType]:
        """
        Process a collection of data items with a single context using the probe operation.

        The probe results for each item are aggregated and collected.

        Args:
            data_collection (DataCollectionType): A collection of data items.
            context (ContextType): The shared context for all items.

        Returns:
            Tuple[DataCollectionType, ContextType]: The original data collection and unchanged context.
        """
        probed_results: List[Any] = []
        parameters = self._get_operation_parameters(context)
        for data_item in data_collection:
            probe_result = self.operation.process(data_item, **parameters)
            probed_results.append(probe_result)
        self.collect(probed_results)
        return data_collection, context

    def _execute_data_collection_context_collection(
        self, data_collection: DataCollectionType, context: ContextCollectionType
    ) -> Tuple[DataCollectionType, ContextCollectionType]:
        """
        Process a collection of data items with a corresponding collection of contexts using the probe operation.

        The probe results are collected across all items.

        Args:
            data_collection (DataCollectionType): A collection of data items.
            context (ContextCollectionType): A collection of contexts.

        Returns:
            Tuple[DataCollectionType, ContextCollectionType]: The original data collection and unchanged context collection.

        Raises:
            ValueError: If the lengths of data_collection and context do not match.
        """
        probed_results: List[Any] = []
        if len(data_collection) != len(context):
            raise ValueError(
                "DataCollectionType and ContextCollectionType must have the same length for parallel slicing."
            )
        for data_item, context_item in zip(data_collection, context):
            parameters = self._get_operation_parameters(context_item)
            probe_result = self.operation.process(data_item, **parameters)
            probed_results.append(probe_result)
        self.collect(probed_results)
        return data_collection, context


def node_factory(
    node_definition: Dict,
    logger: Optional[Logger] = None,
) -> DataNode | ContextNode:
    """
    Factory function to create an appropriate node instance based on the given definition.

    The node definition dictionary should include:
      - "operation": The class (or a string that can be resolved to a class) for the operation.
      - "parameters": (Optional) A dictionary of parameters for the operation.
      - "context_keyword": (Optional) A string specifying the context key for probe injection.

    Args:
        node_definition (Dict): A dictionary describing the node configuration.
        logger (Optional[Logger]): Optional logger instance for diagnostic messages.

    Returns:
        DataNode | ContextNode: An instance of a subclass of DataNode or ContextNode based on the operation type.

    Raises:
        ValueError: If the node definition is invalid or if the operation type is unsupported.
    """

    def get_class(class_name):
        """Helper function to retrieve the class from the loader if the input is a string."""
        if isinstance(class_name, str):
            return ComponentLoader.get_class(class_name)
        return class_name

    operation = node_definition.get("operation")
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    # Resolve the operation class if provided as a string.
    operation = get_class(operation)

    if operation is None or not isinstance(operation, type):
        raise ValueError("operation must be a class type or a string, not None.")

    if issubclass(operation, ContextOperation):
        return ContextNode(operation, operation_config=parameters, logger=logger)

    elif issubclass(operation, DataAlgorithm):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataAlgorithm nodes."
            )
        return AlgorithmNode(
            data_operation=operation,
            operation_parameters=parameters,
            logger=logger,
        )
    elif issubclass(operation, DataProbe):
        if context_keyword is not None:
            return ProbeContextInjectorNode(
                data_operation=operation,
                context_keyword=context_keyword,
                operation_parameters=parameters,
                logger=logger,
            )
        else:
            return ProbeResultCollectorNode(
                data_operation=operation,
                operation_parameters=parameters,
                logger=logger,
            )
    else:
        raise ValueError(
            "Unsupported operation type. Operation must be of type DataAlgorithm or DataProbe."
        )
