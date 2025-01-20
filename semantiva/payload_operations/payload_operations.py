from typing import List, Any, Dict, Optional, Type
from abc import ABC, abstractmethod
from .stop_watch import StopWatch
from ..context_operations.context_operations import (
    ContextOperation,
    ContextType,
    ContextPassthrough,
)
from ..context_operations.context_observer import ContextObserver
from ..data_operations.data_operations import (
    BaseDataOperation,
    DataAlgorithm,
    DataProbe,
)
from ..data_types.data_types import BaseDataType


class PayloadOperation(ContextObserver, ABC):
    """
    Base class for operations involving payloads in the semantic framework.

    This class extends ContextObserver to incorporate context management capabilities
    into payload-related operations.

    Attributes:
        context (dict): Inherited from ContextObserver, stores context key-value pairs.
        data (BaseDataType): An instance of a class derived from BaseDataType.
    """

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

    def __init__(
        self,
        data_operation: Type[BaseDataOperation],
        context_operation: ContextOperation,
        operation_config: Optional[Dict] = None,
    ):
        """
        Initialize a Node with the specified data operation, context operation, and parameters.

        Args:
            data_operation (BaseDataOperation): The data operation associated with this node.
            context_operation (ContextOperation): The context operation for managing context (default: ContextOperation).
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
        """
        super().__init__()
        self.data_operation = (
            data_operation(self)
            if issubclass(data_operation, DataAlgorithm)
            else data_operation()
        )

        self.context_operation = context_operation
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

    A pipeline is a structured sequence of nodes or operations designed to process
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

    def __init__(self, pipeline_configuration: List[Dict]):
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
        super().__init__()
        self.nodes: List[Node] = []
        self.pipeline_configuration: List[str] = pipeline_configuration
        self.stop_watch = StopWatch()
        self._initialize_nodes()

    def _add_node(self, node: Node):
        """
        Add a node to the pipeline.

        Args:
            node (Node): The node to add to the pipeline.
        """
        if self.nodes:
            last_node = self.nodes[-1]
            if isinstance(self.nodes[-1], AlgorithmNode):
                assert (
                    last_node.data_operation.output_data_type()
                    == node.data_operation.input_data_type()
                ), f"Invalid pipeline topology: Output of {last_node.data_operation.__class__.__name__} not compatible with {node.data_operation.__class__.__name__}."
        self.nodes.append(node)

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute the pipeline sequentially with the provided input data and context.

        Args:
            data (BaseDataType): The input data to be processed by the pipeline.
            context (ContextType): The context information to be updated during processing.

        Returns:
            tuple[BaseDataType, ContextType]: A tuple containing the final processed data
                                              and the updated context after pipeline execution.
        """
        self.stop_watch.start()
        result_data, result_context = data, context
        for node in self.nodes:
            result_data, result_context = node.process(result_data, result_context)
        self.stop_watch.stop()
        return result_data, result_context

    def inspect(self) -> str:
        """
        Inspect the current pipeline structure and return its summary, including execution time.

        Returns:
            str: A summary of the pipeline including nodes and their sequence, as well as
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
        summary += f"Pipeline {self.stop_watch}"
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
            node = node_factory(node_config)
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
        context_operation: ContextOperation,
        operation_parameters: Optional[Dict] = None,
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
        super().__init__(data_operation, context_operation, operation_parameters)

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
        context_operation: ContextOperation,
        context_keyword: str,
        operation_parameters: Optional[Dict] = None,
    ):
        """
        Initialize a ProbeContextInjectornode with a data operation and context keyword.

        Args:
            data_operation (BaseDataOperation): The data operation for this node.
            context_keyword (str): The keyword for context injection.
        """
        super().__init__(data_operation, context_operation, operation_parameters)
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
        context_operation: ContextOperation,
        operation_parameters: Optional[Dict] = None,
    ):
        """
        Initialize a ProbeResultCollectorNode with the specified data probe.

        Args:
            data_operation (DataProbe): The data probe for this node.
            context_operation (ContextOperation): The context operation for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
        """
        super().__init__(data_operation, context_operation, operation_parameters)
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


def node_factory(node_definition: Dict) -> Node:
    """
    Factory function to create a Node instance based on the given definition.

    Args:
        node_definition (Dict): A dictionary defining the node structure. Expected keys:
            - "operation": An instance of DataOperation (required).
            - "context_operation": An instance of ContextOperation (optional).
            - "parameters": A dictionary of operation parameters (optional).
            - "context_keyword": A string defining a context keyword (optional).

    Returns:
        Node: An instance of the appropriate Node subclass.

    Raises:
        ValueError: If the node definition is invalid or incompatible.
    """
    operation = node_definition.get("operation")
    context_operation = node_definition.get("context_operation", ContextPassthrough())
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
        )

    elif issubclass(operation, DataProbe):
        if context_keyword is not None:
            return ProbeContextInjectorNode(
                data_operation=operation,
                context_operation=context_operation,
                context_keyword=context_keyword,
                operation_parameters=parameters,
            )
        else:
            return ProbeResultCollectorNode(
                data_operation=operation,
                context_operation=context_operation,
                operation_parameters=parameters,
            )

    else:
        raise ValueError(
            "Unsupported operation type. Operation must be of type DataAlgorithm or DataProbe."
        )
