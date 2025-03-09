from typing import Any, Dict, List, Optional, Tuple
from .stop_watch import StopWatch
from .payload_processors import PayloadProcessor
from .nodes.nodes import (
    DataNode,
    OperationNode,
    ContextNode,
    ProbeResultCollectorNode,
    ProbeContextInjectorNode,
)
from ..logger import Logger
from ..data_types.data_types import BaseDataType, DataCollectionType
from ..data_processors.data_processors import DataOperation
from ..context_processors.context_types import ContextType
from .nodes.node_factory import node_factory


class Pipeline(PayloadProcessor):
    """
    Represents a pipeline for orchestrating multiple payload operations.

    A pipeline is a structured collection of nodes or operations designed to process
    `BaseDataType` data and context in a systematic manner. It enables the execution
    of complex workflows by chaining multiple `Node` instances together.

    Node Configuration:
    Each node in the pipeline is defined using a dictionary with the following keys:

    - `processor` (required): The operation to perform, either a `DataOperation (DataOperation` or `DataProbe`) or a `ContextProcessor`.
    - `parameters` (optional, default=`{}`): A dictionary of parameters for the operation.
      If an operation parameter is **not explicitly defined** in the pipeline configuration,
      it is extracted from the **context**, using the parameter name as the context keyword.
      Parameters explicitly defined in the pipeline configuration take precedence over those
      obtained from the context.

    ### Node Types:

    1. **OperationNode**:
       - Configured when a `DataOperation` is given as the `processor`.
       - Example:
         ```python
         {
             "processor": SomeDataOperation,
             "parameters": {"param1": value1, "param2": value2}
         }
         ```
       - Defaults:
         - `parameters` defaults to an empty dictionary `{}`.

    2. **ProbeContextInjectorNode**:
       - Configured when a `DataProbe` is used as the `processor`, and `context_keyword` is **not** provided.
       - This node collects probe results. No changes in data or context information.
       - Example:
         ```python
         {
             "processor": SomeDataProbe
         }
         ```
       - Defaults:
         - `parameters` defaults to `{}`.

    3. **ProbeResultCollectorNode**:
       - Configured when a `DataProbe` is used as the `processor`, and `context_keyword` **is** provided.
       - Stores collected probe results in the context container under the specified keyword.
       - Example:
         ```python
         {
             "processor": SomeDataProbe,
             "context_keyword": "some_probe_keyword"
         }
         ```
       - Defaults:
         - `parameters` defaults to `{}`.

    ### Data Processing and Slicing:

    The pipeline processes data and context sequentially through its nodes. Processing follows these rules:
        1. If the node's expected input type matches the current data type exactly,
           the node processes the entire data object in a single call. This is the nominal operation.
        2. If the current data is a `DataCollectionType` and the node process its base type,
           data is processed **element-wise** using a slicing stratgy.
        3. If neither condition applies, an error is raised (invalid pipeline topology).

    The pipeline supports both `ContextType` and `ContextCollectionType`:
        - When slicing data, if the context is a `ContextCollectionType`, it is sliced in parallel.
        - If the context is a single `ContextType`, it is **reused** for each data item and the result
          of the context operation is not passed to the next node.

    Attributes:
        pipeline_configuration (List[Dict]): A list of dictionaries defining the configuration
                                             for each node in the pipeline.
        nodes (List[Node]): The list of nodes that make up the pipeline.
        stop_watch (StopWatch): Tracks the execution time of nodes in the pipeline.
    """

    pipeline_configuration: List[Dict]
    nodes: List[DataNode]
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
            logger (Optional[Logger]): An optional logger instance for logging pipeline activities.

        Example:
            pipeline_configuration = [
                {"processor": SomeDataOperation, "parameters": {"param1": value1}},
                {"processor": SomeDataProbe, "context_keyword": "collected_data"}
            ]
        """
        super().__init__(logger)
        self.nodes: List[DataNode] = []
        self.pipeline_configuration: List[Dict] = pipeline_configuration
        self.stop_watch = StopWatch()
        self._initialize_nodes()
        if self.logger:
            self.logger.info(f"Initialized {self.__class__.__name__}")
            self.logger.debug("%s", self.inspect())

    def _add_node(self, node: DataNode):
        """
        Adds a node to the pipeline while ensuring compatibility between consecutive operations.

        This method enforces that the output type of the last `OperationNode` is compatible
        with the input type of the new node. Probe nodes do not modify data, so their output
        type is ignored for validation purposes.

        If the first node in the pipeline is a probe node, it is added without validation.

        Args:
            node (Node): The node to be added to the pipeline.

        Raises:
            AssertionError: If the input type of the new node is not compatible with the
                            output type of the last `OperationNode`.
        """

        def _get_base_type(
            data_type: type[BaseDataType] | type[DataCollectionType],
        ) -> type[BaseDataType]:
            """Returns the base type if data_type is a DataCollectionType, else returns data_type."""
            if isinstance(data_type, type) and issubclass(
                data_type, DataCollectionType
            ):
                return data_type.collection_base_type()
            return data_type

        # Find the last node that constrains the data type (i.e., last OperationNode)
        last_type_constraining_node: OperationNode | None = None
        for previous_node in reversed(self.nodes):
            if isinstance(previous_node, OperationNode):
                last_type_constraining_node = previous_node
                break

        # If no OperationNode exists yet, allow the first node to be added unconditionally
        if last_type_constraining_node is None or issubclass(type(node), ContextNode):
            self.nodes.append(node)
            return

        # Get the output type of the last type-constraining node and the input type of the new node
        assert isinstance(last_type_constraining_node.processor, DataOperation)
        # Get the base type of the output and input data types if they are DataCollectionType
        output_type = _get_base_type(
            last_type_constraining_node.processor.output_data_type()
        )
        input_type = _get_base_type(node.processor.input_data_type())
        # Enforce strict type matching otherwise
        assert issubclass(output_type, input_type) or issubclass(
            input_type, output_type
        ), (
            f"Invalid pipeline topology: Output of "
            f"{last_type_constraining_node.processor.__class__.__name__} "
            f"({output_type}) not compatible with "
            f"{node.processor.__class__.__name__} ({input_type})."
        )

        # Add the node if it passes validation
        self.nodes.append(node)

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Executes the pipeline by processing data and context sequentially through each node.

        Processing follows these rules:
            1. If the node's expected input type matches the current data type exactly,
            the node processes the entire dataset in a single call.
            2. If the current data is a `DataCollectionType` and the node expects its base type,
            data is processed **element-wise** using `_slicing_strategy`.
            3. If neither condition applies, an error is raised (invalid pipeline topology).

        The pipeline supports both `ContextType` and `ContextCollectionType`:
            - When slicing data, if the context is a `ContextCollectionType`, it is sliced in parallel.
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
        self.logger.info("Start processing pipeline")
        for index, node in enumerate(self.nodes, start=1):
            self.logger.debug(
                f"Processing node {index}: {type(node.processor).__name__} ({type(node).__name__})"
            )
            self.logger.debug(f"    Data: {result_data}, Context: {result_context}")
            # Get the expected input type for the node's operation
            input_type = node.processor.input_data_type()

            if (
                (type(result_data) == input_type)
                or (
                    isinstance(result_data, DataCollectionType)
                    and input_type == result_data.collection_base_type()
                )
                or (issubclass(type(result_data), input_type))
            ):
                result_data, result_context = node.process(result_data, result_context)

            # Case 2: Incompatible data type
            else:
                raise TypeError(
                    f"Incompatible data type for Node {node.processor.__class__.__name__} "
                    f"expected {input_type}, but received {type(result_data)}."
                )
        self.stop_watch.stop()
        self.logger.info("Pipeline execution complete.")
        self.logger.debug(
            "Pipeline execution timing report: \n\tPipeline %s\n%s",
            str(self.stop_watch),
            self.get_timers(),
        )
        return result_data, result_context

    def inspect(self) -> str:
        """
        Return a comprehensive summary of the pipeline's structure, including details about
        each node, how parameters are derived, any context modifications, and total
        execution time.

        The summary covers:
        • Node details: The class names of the nodes and their operations.
        • Parameters: Which parameters come from the pipeline configuration versus the
            context.
        • Context updates: The keywords that each node creates or modifies in the context.
        • Required context keys: The set of context parameters necessary for the pipeline.
        • Execution time: The pipeline's cumulative execution time, tracked by the StopWatch.

        Returns:
            str: A formatted report describing the pipeline composition and relevant details.
        """

        def format_set(values: set[str] | List[str]) -> str:
            """Return a comma-separated string of sorted set items or 'None' if empty."""
            return ", ".join(sorted(values)) if values else "None"

        summary_lines = ["Pipeline Structure:"]
        all_required_params = set()
        probe_injector_keywords = set()

        for index, node in enumerate(self.nodes, start=1):
            # Gather parameter details from node operation
            operation_param_names = set(node.processor.get_processing_parameter_names())
            config_param_names = set(node.processor_config.keys())
            context_param_names = operation_param_names - config_param_names

            # Keep track of any ProbeContextInjectorNode keyword to exclude it from "required" lists
            if isinstance(node, ProbeContextInjectorNode):
                probe_injector_keywords.add(node.context_keyword)

            # Add these context param names to the global set of required keys
            all_required_params.update(context_param_names)

            # Prepare a string of explicitly configured parameters with their assigned values
            if node.processor_config:
                config_with_values = ", ".join(
                    f"{key}={value}" for key, value in node.processor_config.items()
                )
            else:
                config_with_values = "None"

            # Build up a textual summary of this node
            lines_for_node = [
                f"\n\t{index}. Node: {node.processor.__class__.__name__} ({node.__class__.__name__})",
                f"\t\tParameters: {format_set(operation_param_names)}",
                f"\t\t\tFrom pipeline configuration: {config_with_values}",
                f"\t\t\tFrom context: {format_set(context_param_names - probe_injector_keywords)}",
                f"\t\tContext additions: {format_set(node.get_created_keys())}",
            ]
            summary_lines.extend(lines_for_node)

        # Determine which context keys are still needed, excluding those created by probe injector nodes
        needed_context_keys = all_required_params - probe_injector_keywords

        summary_lines.insert(
            1, f"\tRequired context keys: {format_set(needed_context_keys)}"
        )

        # Return the final summary as one string
        return "\n".join(summary_lines)

    def get_timers(self) -> str:
        """
        Retrieve timing information for each node's execution.

        Returns:
            str: A formatted string displaying node number, operation name,
                elapsed CPU time, and elapsed wall time for each node.
        """
        timer_info = [
            f"\t\tNode {i + 1}: {type(node.processor).__name__}; "
            f"\tElapsed CPU Time: {node.stop_watch.elapsed_cpu_time():.6f}s; "
            f"\tElapsed Wall Time: {node.stop_watch.elapsed_wall_time():.6f}s"
            for i, node in enumerate(self.nodes)
        ]
        return "\n".join(timer_info)

    def get_probe_results(self) -> Dict[str, List[Any]]:
        """
        Retrieve the collected data from all probe collector nodes in the pipeline.

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
                probe_results[f"Node {i + 1}/{type(node.processor).__name__}"] = (
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

        for index, node_config in enumerate(self.pipeline_configuration, start=1):
            node = node_factory(node_config, self.logger)
            self.logger.info(f"Initialized Node {index}: {type(node).__name__}")
            self._add_node(node)
