from typing import List, Any, Dict, Optional
from abc import ABC, abstractmethod
from .stop_watch import StopWatch
from ..context_operations.context_operations import ContextOperation, ContextType
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
    def _process(self, *args, **kwargs): ...

    def process(self, *args, **kwargs):
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
        return self._process(*args, **kwargs)


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
        data_operation: BaseDataOperation,
        context_operation: ContextOperation,
        operation_parameters: Optional[Dict] = None,
    ):
        """
        Initialize a Node with the specified data operation, context operation, and parameters.

        Args:
            data_operation (BaseDataOperation): The data operation associated with this node.
            context_operation (ContextOperation): The context operation for managing context (default: ContextOperation).
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
        """
        super().__init__()
        self.data_operation = data_operation
        self.context_operation = context_operation
        if operation_parameters is None:
            self.operation_config = {}
        else:
            self.operation_config = operation_parameters

    def _process(
        self, data: Any, context: ContextType
    ) -> tuple[BaseDataType, ContextType]:
        """
        Execute the data operation associated with this node.

        Args:
            data (Any): Input data for the operation.
            context (ContextType): Contextual information required for execution.

        Returns:
            BaseDataType: The processed output data.
            ContextType: Updated context after execution.
        """
        self.stop_watch.start()
        parameters = self._get_operation_parameters(context)
        output_data = self.data_operation.process(data, **parameters)
        self.stop_watch.stop()
        return output_data

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


class Pipeline(PayloadOperation):
    """
    Represents a pipeline for orchestrating multiple payload operations.

    A pipeline is a sequence of nodes or operations that processes data in a structured
    manner. It facilitates the execution of complex workflows.

    Attributes:
        nodes (List[Node]): The sequence of nodes in the pipeline.
        node_sequence (List[str]): The sequence of node names in topological order.
    """

    def __init__(self):
        """
        Initialize an empty pipeline.
        """
        super().__init__()
        self.nodes: List[Node] = []
        self.node_sequence: List[str] = []

    def add_node(self, node: Node):
        """
        Add a node to the pipeline.

        Args:
            node (Node): The node to add.
        """
        self.nodes.append(node)

    def _process(self, data: Any, context: ContextType) -> tuple[Any, ContextType]:
        """
        Execute the pipeline with the provided input data.

        Args:
            data (Any): Input data for the pipeline.

        Returns:
            Any: The result of the pipeline execution.
        """
        result = data
        for node in self.nodes:
            result = node.process(result, context)
        return result

    def inspect(self) -> str:
        """
        Inspect the current pipeline structure and return its summary.

        Returns:
            str: A summary of the pipeline including nodes and their sequence.
        """
        summary = "Pipeline Structure:\n"
        for i, node in enumerate(self.nodes):
            summary += f"{i + 1}. Node: {node.__class__.__name__}, Operation: {type(node.data_operation).__name__}\n"
        return summary

    def get_timers(self) -> dict:
        """
        Retrieve timing information for each node's execution (mock implementation).

        Returns:
            dict: A dictionary with node names as keys and execution times as values.
        """
        # Mock implementation for timing
        timers = {f"Node {i + 1}": 0.1 * (i + 1) for i in range(len(self.nodes))}
        return timers

    def _check_node_topology(self):
        """
        Check the topological order of nodes to ensure the pipeline is valid.

        Raises:
            ValueError: If the topology is invalid.
        """
        if not self.nodes:
            raise ValueError("Pipeline has no nodes to check topology.")
        self.node_sequence = [f"Node {i + 1}" for i in range(len(self.nodes))]

    def _initialize_nodes(self):
        """
        Initialize all nodes in the pipeline (mock implementation).
        """
        for node in self.nodes:
            # Mock initialization logic
            print(f"Initializing node: {node.__class__.__name__}")


class AlgorithmNode(Node):
    """
    A specialized node for executing algorithmic operations.

    Attributes:
        data_operation (DataAlgorithm): The data algorithm associated with the node.
    """

    def __init__(
        self,
        data_operation: DataAlgorithm,
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
        super().__init__(data_operation, context_operation, operation_parameters)


class ProbeNode(Node):
    """
    A specialized node for probing data within the framework.

    Attributes:
        data_operation (DataProbe): The data probe operation associated with the node.
        context_operation (ContextOperation): The context operation associated with node.
        operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
    """

    def __init__(
        self,
        data_operation: DataProbe,
        context_operation: ContextOperation,
        operation_parameters: Optional[Dict] = None,
    ):
        """
        Initialize a ProbeNode with the specified data probe.

        Args:
            data_operation (DataProbe): The data probe for this node.
            context_operation (ContextOperation): The context operation for this node.
        """
        super().__init__(data_operation, context_operation, operation_parameters)


class ProbeContextInjectornode(Node):
    """
    A node for injecting context-related information into the semantic framework.

    Attributes:
        data_operation (DataProbe): The data probe for this node.
        context_operation (ContextOperation): The context operation for this node.
        context_keyword (str): The keyword used for injecting context information.
        operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
    """

    def __init__(
        self,
        data_operation: BaseDataOperation,
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

    def inject_context(self, value: Any):
        """
        Inject a value into the context using the context keyword.

        Args:
            value (Any): The value to inject into the context.
        """
        if not self.context_keyword:
            raise ValueError("Context keyword is not set or invalid.")
        self.update_context(self.context_keyword, value)


class ProbeResultColectorNode(Node):
    """
    A node for collecting probed data during operations.

    Attributes:
        _probed_data (List[Any]): A list of data collected during probing operations.
    """

    def __init__(
        self,
        data_operation: DataProbe,
        context_operation: ContextOperation,
        operation_parameters: Optional[Dict] = None,
    ):
        """
        Initialize a ProbeResultColectorNode with the specified data probe.

        Args:
            data_operation (DataProbe): The data probe for this node.
            context_operation (ContextOperation): The context operation for this node.
            operation_parameters (Optional[Dict]): Initial configuration for operation parameters (default: None).
        """
        super().__init__(data_operation, context_operation, operation_parameters)
        self._probed_data: List[Any] = []

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
