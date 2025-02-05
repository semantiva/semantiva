from typing import List, Any, Dict, Optional, Type
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

from ..context_operations.context_types import ContextType

from ..data_types.data_types import BaseDataType
from ..logger import Logger
from .payload_operations import PayloadOperation


class Node(PayloadOperation):
    """
    Represents a node in the semantic framework.

    A node is associated with a data operation and acts as a fundamental unit
    in processing pipelines or networks.

    Attributes:
        data_operation (BaseDataOperation): The data operation associated with the node.
        context_operation (ContextOperation): Handles the contextual aspects of the node.
        operation_config (Dict): Configuration parameters for the data operation.
        stop_watch (StopWatch): Tracks the execution time of the node's operation.
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
            data_operation (BaseDataOperation): The data operation associated with this node.
            context_operation (ContextOperation): The context operation for managing context.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
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
        if operation_config is None:
            self.operation_config = {}
        else:
            self.operation_config = operation_config

    def _get_operation_parameters(self, context: ContextType) -> dict:
        """
        Retrieve the parameters required for the associated data operation.

        Args:
            context (ContextType): Contextual information used to resolve parameter values.

        Returns:
            dict: A dictionary of parameter names and their corresponding values.
        """
        parameter_names = self.data_operation.get_operation_parameter_names()
        parameters = {}

        for name in parameter_names:
            parameters[name] = self._fetch_parameter_value(name, context)

        return parameters

    def _fetch_parameter_value(self, name: str, context: ContextType) -> Any:
        """
        Fetch parameter values based on the operation configuration or context.

        Args:
            name (str): The name of the parameter to fetch.
            context (ContextType): Contextual information for resolving parameter values.

        Returns:
            Any: The value of the parameter, prioritizing `operation_config` over `context`.
        """
        if name in self.operation_config.keys():
            return self.operation_config[name]
        else:
            return context.get_value(name)

    def __str__(self) -> str:
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     data_operation={self.data_operation},\n"
            f"     context_operation={self.context_operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}"
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
            data_operation (DataAlgorithm): The data algorithm for this node.
            context_operation (ContextOperation): The context operation for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
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

        This method handles the processing of data using the associated data operation
        and updates the context using the provided context operation.

        Args:
            data (BaseDataType): Input data for the operation.
            context (ContextType): Contextual information required for execution.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing:
                - The processed output data (BaseDataType).
                - The updated context after execution (ContextType).
        """
        # Start the stopwatch to measure execution time
        self.stop_watch.start()

        # Update the context using the context operation
        self.observer_context = self.context_operation.operate_context(context)

        # Retrieve operation parameters from the context
        parameters = self._get_operation_parameters(self.observer_context)

        # Perform the data operation
        output_data = self.data_operation.process(data, **parameters)

        # Stop the stopwatch after execution
        self.stop_watch.stop()

        return output_data, self.observer_context


class ProbeNode(Node):
    """
    A specialized node for probing data within the framework.
    """


class ProbeContextInjectorNode(ProbeNode):
    """
    A node for injecting context-related information into the semantic framework.

    Attributes:
        data_operation (DataProbe): The data probe for this node.
        context_operation (ContextOperation): The context operation for this node.
        context_keyword (str): The keyword used for injecting context information.
        operation_parameters (Optional[Dict]): Configuration for operation parameters (default: None).
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
        Initialize a ProbeContextInjectornode with a data operation and context keyword.

        Args:
            data_operation (BaseDataOperation): The data operation for this node.
            context_keyword (str): The keyword for context injection.
        """
        super().__init__(
            data_operation, context_operation, operation_parameters, logger
        )
        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")
        self.context_keyword = context_keyword

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute the data probe operation with context injection.

        This method inspects the data using the associated data probe, injects the
        result into the context using a specified context keyword, and updates the
        context using the provided context operation.

        Args:
            data (BaseDataType): Input data to be probed.
            context (ContextType): Contextual information required for execution.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing:
                - The original input data (unchanged).
                - The updated context after execution (ContextType).
        """
        # Start the stopwatch to measure execution time
        self.stop_watch.start()

        # Update the context using the context operation
        updated_context = self.context_operation.operate_context(context)

        # Retrieve operation parameters from the context
        parameters = self._get_operation_parameters(updated_context)

        # Perform the probing operation and inject the result into the context
        probe_result = self.data_operation.process(data, **parameters)
        updated_context.set_value(self.context_keyword, probe_result)

        # Stop the stopwatch after execution
        self.stop_watch.stop()

        return data, updated_context

    def __str__(self) -> str:
        class_name = self.__class__.__name__
        return (
            f"{class_name}(\n"
            f"     data_operation={self.data_operation},\n"
            f"     context_keyword={self.context_keyword},\n"
            f"     context_operation={self.context_operation},\n"
            f"     operation_config={self.operation_config},\n"
            f"     Node execution summary: {self.stop_watch}"
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
            data_operation (DataProbe): The data probe for this node.
            context_operation (ContextOperation): The context operation for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
        """
        super().__init__(
            data_operation, context_operation, operation_parameters, logger
        )
        self._probed_data: List[Any] = []

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute the data probe operation and collect the result.

        This method inspects the data using the associated data probe, collects the
        result, and updates the context using the provided context operation.

        Args:
            data (BaseDataType): Input data to be probed.
            context (ContextType): Contextual information required for execution.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing:
                - The original input data (unchanged).
                - The updated context after execution (ContextType).
        """
        # Start the stopwatch to measure execution time
        self.stop_watch.start()

        # Update the context using the context operation
        updated_context = self.context_operation.operate_context(context)

        # Retrieve operation parameters from the context
        parameters = self._get_operation_parameters(updated_context)

        # Perform the probing operation and collect the result
        probe_result = self.data_operation.process(data, **parameters)
        self.collect(probe_result)

        # Stop the stopwatch after execution
        self.stop_watch.stop()

        return data, updated_context

    def collect(self, data: Any):
        """
        Collect data from the probe operation.

        Args:
            data (Any): The data to collect.
        """
        self._probed_data.append(data)

    def get_collected_data(self) -> List[Any]:
        """
        Retrieve all collected data.

        Returns:
            List[Any]: The list of collected data.
        """
        return self._probed_data

    def clear_collected_data(self):
        """
        Clear all collected data for reuse in iterative processes.
        """
        self._probed_data.clear()


def node_factory(node_definition: Dict, logger: Optional[Logger] = None) -> Node:
    """
    Factory function to create a Node instance based on the given definition.

    Args:
        node_definition (Dict): A dictionary defining the node structure. Expected keys:
            - "operation": An instance of DataOperation (required).
            - "context_operation": An instance of ContextOperation (optional).
            - "parameters": A dictionary of operation parameters (optional).
            - "context_keyword": A string defining a context keyword (optional).
        logger (Optional[Logger]): A logging instance for debugging or operational logging. Can be `None`.

    Returns:
        Node: An instance of the appropriate Node subclass.

    Raises:
        ValueError: If the node definition is invalid or incompatible.
    """
    operation = node_definition.get("operation")
    context_operation = node_definition.get("context_operation", ContextPassthrough)
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    # Check if operation is valid (not None and a class type)
    if operation is None or not isinstance(operation, type):
        raise ValueError("operation must be a class type, not None.")

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
