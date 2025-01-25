from typing import List, Any, Dict, Optional, Type, Tuple
from abc import ABC, abstractmethod
from .stop_watch import StopWatch
from ..context_operations.context_operations import (
    ContextOperation,
    ContextPassthrough,
)

from ..context_operations.context_types import ContextType, ContextCollectionType
from ..context_operations.context_observer import ContextObserver
from ..data_operations.data_operations import (
    BaseDataOperation,
    DataAlgorithm,
    DataProbe,
)
from ..data_types.data_types import BaseDataType, DataCollectionType
from ..logger import Logger


class PayloadOperation(ContextObserver, ABC):
    """
    Base class for operations involving payloads in the semantic framework.

    This class extends ContextObserver to incorporate context management capabilities
    into payload-related operations.

    Attributes:
        context (dict): Inherited from ContextObserver, stores context key-value pairs.
        data (BaseDataType): An instance of a class derived from BaseDataType.
    """

    logger: Logger

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__()
        if logger:
            # If a logger instance is provided, use it
            self.logger = logger
        else:
            # If no logger is provided, create a new Logger instance
            self.logger = Logger()

    @abstractmethod
    def _process(self, data: BaseDataType, context: ContextType): ...

    def process(
        self, data: BaseDataType, context: ContextType | dict[Any, Any]
    ) -> tuple[BaseDataType, ContextType]:
        """
        Public method to execute the payload processing logic.

        This method serves as an entry point to invoke the concrete implementation
        of the `_process` method, which must be defined in subclasses.

        Args:
            *args: Variable-length positional arguments to be passed to the `_process` method.
            **kwargs: Variable-length keyword arguments to be passed to the `_process` method.

        Returns:
            Any: The result of the `_process` method, as determined by the subclass implementation.

        Raises:
            NotImplementedError: If the `_process` method is not implemented in a subclass.
        """
        context_ = ContextType(context) if isinstance(context, dict) else context
        return self._process(data, context_)


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
        self.data_operation = (
            data_operation(self, logger)
            if issubclass(data_operation, DataAlgorithm)
            else data_operation(logger=logger)
        )

        self.context_operation = context_operation()
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


class Pipeline(PayloadOperation):
    """
    Represents a pipeline for orchestrating multiple payload operations.

    A pipeline is a structured collecton of nodes or operations designed to process
    `BaseDataType` data and context in a systematic manner. It enables the execution
    of complex workflows by chaining multiple `Node` instances together.

    Attributes:
        pipeline_configuration (List[Dict]): A list of dictionaries defining the configuration
                                             for each node in the pipeline.
        nodes (List[Node]): The list of nodes that make up the pipeline.
        stop_watch (StopWatch): Tracks the execution time of the pipeline.
    """

    pipeline_configuration: List[Dict]
    nodes: List[Node]
    stop_watch: StopWatch

    def __init__(
        self, pipeline_configuration: List[Dict], logger: Optional[Logger] = None
    ):
        """
        Initialize a pipeline based on the provided configuration.

        Args:
            pipeline_configuration (List[Dict]): A list of dictionaries where each dictionary
                                                 specifies the configuration for a node in the
                                                 pipeline.

        Example:
            pipeline_configuration = [
                {"operation": DataAlgorithm, "context_operation": ContextOperation, "parameters": {}},
                {"operation": DataProbe, "context_operation": ContextOperation, "parameters": {}}
            ]
        """
        super().__init__(logger)
        self.nodes: List[Node] = []
        self.pipeline_configuration: List[str] = pipeline_configuration
        self.stop_watch = StopWatch()
        self._initialize_nodes()
        self.logger.debug("%s", self.inspect())

    def _add_node(self, node: Node):
        """
        Adds a node to the pipeline while ensuring compatibility between consecutive operations.

        This method enforces that the output type of the last `AlgorithmNode` is compatible
        with the input type of the new node. Probe nodes do not modify data, so their output
        type is ignored for validation purposes.

        If the first node in the pipeline is a probe node, it is added without validation.

        Args:
            node (Node): The node to be added to the pipeline.

        Raises:
            AssertionError: If the input type of the new node is not compatible with the
                            output type of the last `AlgorithmNode`.
        """
        # Find the last node that constrains the data type (i.e., last AlgorithmNode)
        last_type_constraining_node = None
        for previous_node in reversed(self.nodes):
            if isinstance(previous_node, AlgorithmNode):
                last_type_constraining_node = previous_node
                break

        # If no AlgorithmNode exists yet, allow the first node to be added unconditionally
        if last_type_constraining_node is None:
            self.nodes.append(node)
            return

        # Get the output type of the last type-constraining node and the input type of the new node
        output_type = last_type_constraining_node.data_operation.output_data_type()
        input_type = node.data_operation.input_data_type()

        # If the output is a DataCollecton, check its base type
        if isinstance(output_type, type) and issubclass(
            output_type, DataCollectionType
        ):
            base_type = output_type.collection_base_type()

            # Allow the node if the base type matches the input type
            if base_type == input_type:
                self.nodes.append(node)
                return

        # Enforce strict type matching otherwise
        assert (
            output_type == input_type
        ), f"Invalid pipeline topology: Output of {last_type_constraining_node.data_operation.__class__.__name__} ({output_type}) not compatible with {node.data_operation.__class__.__name__} ({input_type})."

        # Add the node if it passes validation
        self.nodes.append(node)

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Executes the pipeline by processing data and context sequentially through each node.

        Processing follows these rules:
            1. If the node’s expected input type matches the current data type exactly,
            the node processes the entire dataset in a single call.
            2. If the current data is a `DataCollecton` and the node expects its base type,
            data is processed **element-wise** using `_slicing_strategy`.
            3. If neither condition applies, an error is raised (invalid pipeline topology).

        The pipeline supports both `ContextType` and `ContextCollectonType`:
            - When slicing data, if the context is a `ContextCollectonType`, it is sliced in parallel.
            - If the context is a single `ContextType`, it is **reused** for each data item.

        Args:
            data (BaseDataType): The initial input data for the pipeline.
            context (ContextType): The initial context, which may be updated during processing.

        Returns:
            Tuple[BaseDataType, ContextType]: The final processed data and context.

        Raises:
            TypeError: If the node's expected input type does not match the current data type.
        """
        self.stop_watch.start()
        result_data, result_context = data, context
        self.logger.debug("Start processing pipeline")
        for node in self.nodes:
            self.logger.debug(
                f"Processing {type(node.data_operation).__name__} ({type(node).__name__})"
            )
            # Get the expected input type for the node's operation
            input_type = node.data_operation.input_data_type()

            # Case 1: Exact match → process the full data in a single step
            if type(result_data) == input_type:
                result_data, result_context = node.process(result_data, result_context)

            # Case 2: Data is a `DataCollecton` and node expects its base type → use slicing
            elif (
                isinstance(result_data, DataCollectionType)
                and input_type == result_data.collection_base_type()
            ):
                result_data, result_context = self._slicing_strategy(
                    node, result_data, result_context
                )

            # Case 3: Incompatible data type
            else:
                raise TypeError(
                    f"Incompatible data type for Node {node.data_operation.__class__.__name__} "
                    f"expected {input_type}, but received {type(result_data)}."
                )

        self.stop_watch.stop()
        self.logger.debug("Finished pipeline")
        self.logger.debug(
            f"Pipeline timers \nPipeline {self.stop_watch}\n{self.get_timers()}"
        )  # TODO: use lazy evaluation
        return result_data, result_context

    def _slicing_strategy(
        self, node: Node, data_collecton: DataCollectionType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Processes a `DataCollecton` element-wise, slicing context when applicable.

        This method ensures that:
            - If `context` is a `ContextCollectonType`, its elements are used in parallel with data items.
            - If `context` is a single `ContextType`, it is **reused** for each data item.

        The resulting processed data is stored in a new collecton of the same type.

        Args:
            node (Node): The pipeline node performing the operation.
            data_collecton (DataCollecton): The collecton of data elements to be processed.
            context (ContextType): Either a `ContextType` or `ContextCollectonType`.

        Returns:
            Tuple[BaseDataType, ContextType]:
                - A new `DataCollecton` containing the processed elements.
                - A `ContextCollectonType` if slicing was applied, or a single updated `ContextType` otherwise.

        Raises:
            ValueError: If `ContextCollectonType` and `DataCollecton` lengths do not match.
        """
        # Initialize a new collecton to store processed results
        processed_data_collecton = type(data_collecton)()

        if isinstance(context, ContextCollectionType):
            # Ensure both collectons have the same length before parallel slicing
            if len(data_collecton) != len(context):
                raise ValueError(
                    "DataCollecton and ContextCollectonType must have the same length for parallel slicing."
                )

            # Create a new `ContextCollectonType` to store results
            processed_context_collecton = ContextCollectionType()

            # Process (data_item, context_item) pairs in parallel
            for d_item, c_item in zip(data_collecton, context):
                out_data, out_context = node.process(d_item, c_item)
                processed_data_collecton.append(out_data)
                processed_context_collecton.append(out_context)

            return processed_data_collecton, processed_context_collecton

        else:
            # Context is a single instance, reuse it for each data item
            current_context = context
            self.logger.warning("Context operations in this slicing mode are lost.")
            for d_item in data_collecton:
                out_data, current_context = node.process(d_item, current_context)
                processed_data_collecton.append(out_data)

            return processed_data_collecton, current_context

    def inspect(self) -> str:
        """
        Inspect the current pipeline structure and return its summary, including execution time.

        Returns:
            str: A summary of the pipeline including nodes and their collecton, as well as
                 the total pipeline execution time.
        """

        # Format sets as comma-separated values instead of Python set syntax
        def format_set(s):
            return ", ".join(sorted(s)) if s else "None"

        summary = "Pipeline Structure:\n"

        all_context_params = set()
        probe_injector_params = set()
        node_summary = ""
        for i, node in enumerate(self.nodes):

            operation_params = set(node.data_operation.get_operation_parameter_names())
            node_config_params = set(node.operation_config.keys())
            context_params = operation_params - node_config_params

            if isinstance(node, ProbeContextInjectorNode):
                probe_injector_params.add(node.context_keyword)

            all_context_params.update(context_params)

            # Extract configuration parameters with their values
            config_with_values = (
                ", ".join(
                    f"{key}={value}" for key, value in node.operation_config.items()
                )
                if node.operation_config
                else "None"
            )
            node_summary += f"{i + 1}. Node: {node.data_operation.__class__.__name__}({node.__class__.__name__})\n"
            node_summary += f"\tParameters: {format_set(operation_params)}\n"
            node_summary += (
                f"\t\tFrom pipeline configuration: {config_with_values or None}\n"
            )
            node_summary += f"\t\tFrom context: {format_set(context_params - probe_injector_params) or None}\n"

        # Determine the final values needed in the context
        needed_context_parameters = all_context_params - probe_injector_params
        summary += f"Context parameters needed: {format_set(needed_context_parameters) or None}\n"
        summary += node_summary
        # summary += f"Pipeline {self.stop_watch}"
        return summary

    def get_timers(self) -> str:
        """
        Retrieve timing information for each node's execution.

        Returns:
            str: A formatted string displaying node number, operation name,
                elapsed CPU time, and elapsed wall time for each node.
        """
        timer_info = [
            f"Node {i + 1}: {type(node.data_operation).__name__}; "
            f"Elapsed CPU Time: {node.stop_watch.elapsed_cpu_time():.6f}s; "
            f"Elapsed Wall Time: {node.stop_watch.elapsed_wall_time():.6f}s"
            for i, node in enumerate(self.nodes)
        ]
        return "\n".join(timer_info)

    def get_probe_results(self) -> Dict[str, List[Any]]:
        """
        Retrieve the collected data from all probe nodes in the pipeline.

        This method iterates through the pipeline's nodes and checks for instances of
        `ProbeResultCollectorNode`. For each such node, it retrieves the collected data and
        associates it with the corresponding node's index in the pipeline.

        Returns:
            Dict[str, List[Any]]: A dictionary where keys are node identifiers (e.g., "Node 1/ProbeName"),
            and values are the collected data from the probe nodes.

        Example:
            If Node 1 and Node 3 are probe nodes, the result might look like:
            {
                "Node 1/ProbeName": [<collected_data_1>],
                "Node 3/ProbeName": [<collected_data_3>]
            }
        """
        # Dictionary to store probe results keyed by node identifiers
        probe_results = {}

        # Iterate over all nodes in the pipeline
        for i, node in enumerate(self.nodes):
            # Check if the node is a ProbeResultCollectorNode
            if isinstance(node, ProbeResultCollectorNode):
                # Add the collected data from the node to the results dictionary
                probe_results[f"Node {i + 1}/{type(node.data_operation).__name__}"] = (
                    node.get_collected_data()
                )

        # Return the dictionary of probe results
        return probe_results

    def _initialize_nodes(self):
        """
        Initialize all nodes in the pipeline.

        This method uses the `node_factory` function to create nodes from the provided
        pipeline configuration. Each node is then added to the pipeline.
        """
        for node_config in self.pipeline_configuration:
            node = node_factory(node_config, self.logger)
            self._add_node(node)


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
