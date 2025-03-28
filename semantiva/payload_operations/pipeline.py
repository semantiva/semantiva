from typing import Any, Dict, List, Optional, Tuple
from semantiva.exceptions.pipeline import (
    PipelineConfigurationError,
    PipelineTopologyError,
)
from .payload_processors import PayloadProcessor
from .nodes.nodes import (
    PipelineNode,
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
        self.nodes = self._initialize_nodes()
        if self.logger:
            self.logger.info(f"Initialized {self.__class__.__name__}")
            self.logger.debug("%s", self.inspect())

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Executes the pipeline by processing data and context sequentially through each node.


        Args:
            data (BaseDataType): The initial input data for the pipeline.
            context (ContextType): The initial context, which may be updated during processing.

        Returns:
            Tuple[BaseDataType, ContextType]: The final processed data and context.

        Raises:
            TypeError: If the node's expected input type does not match the current data type.
        """

        result_data, result_context = data, context
        self.logger.info("Start processing pipeline")
        for index, node in enumerate(self.nodes, start=1):
            self.logger.debug(
                f"Processing node {index}: {type(node.processor).__name__} ({type(node).__name__})"
            )
            self.logger.debug(f"    Data: {result_data}, Context: {result_context}")
            # Get the expected input type for the node's operation
            input_type = node.processor.input_data_type()

            if issubclass(type(result_data), input_type):
                result_data, result_context = node.process(result_data, result_context)

            # Case 2: Incompatible data type
            else:
                raise TypeError(
                    f"Incompatible data type for Node {node.processor.__class__.__name__} "
                    f"expected {input_type}, but received {type(result_data)}."
                )

        self.logger.info("Pipeline execution complete.")
        self.logger.debug(
            "Pipeline execution timing report: \n\tPipeline %s\n%s",
            str(self.stop_watch),
            self.get_timers(),
        )
        return result_data, result_context

    def inspect(self) -> str:
        """
        Return a comprehensive summary of the pipeline's structure.
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
        summary_lines = ["Pipeline Structure:"]
        # All context keys required by the pipeline
        all_required_params: set[str] = set()
        # Context keys injected or created by the pipeline
        injected_or_created_keywords: set[str] = set()
        # Context keys deleted by the pipeline
        deleted_keys: set[str] = set()

        for index, node in enumerate(self.nodes, start=1):
            node_summary = self._build_node_summary(
                node,
                index,
                deleted_keys,
                all_required_params,
                injected_or_created_keywords,
            )
            summary_lines.extend(node_summary)

        # Calculate the context keys required by the pipeline
        required_context_keys = self._calculate_required_context_keys(
            all_required_params, injected_or_created_keywords
        )
        # Add the required context keys to the summary
        summary_lines.insert(
            1, f"\tRequired context keys: {self._format_set(required_context_keys)}"
        )

        return "\n".join(summary_lines)

    # --- Extracted Helper Methods ---

    def _format_set(self, values: set[str] | list[str]) -> str:
        """Return a comma-separated string of sorted set items or 'None' if empty."""
        return ", ".join(sorted(values)) if values else "None"

    def _build_node_summary(
        self,
        node: PipelineNode,
        index: int,
        deleted_keys: set[str],
        all_required_params: set[str],
        injected_or_created_keywords: set[str],
    ) -> list[str]:
        """Build a summary for a single node, updating tracking sets."""
        # Extract operation parameters and configuration parameters

        operation_params = set(node.processor.get_processing_parameter_names())
        config_params = set(node.processor_config.keys())
        # context parameters are operation parameters not in the configuration
        context_params = operation_params - config_params

        all_required_params.update(context_params)
        created_keys = node.processor.get_created_keys()
        injected_or_created_keywords.update(created_keys)

        # If the node is a ProbeContextInjectorNode, add the context keyword to the set
        if isinstance(node, ProbeContextInjectorNode):
            injected_or_created_keywords.add(node.context_keyword)

        # Validate if the node requires keys previously deleted
        # but not present in the configuration
        self._validate_deleted_keys(
            index, operation_params, config_params, deleted_keys
        )

        node_summary_lines = [
            f"\n\t{index}. Node: {node.processor.__class__.__name__} ({node.__class__.__name__})",
            f"\t\tParameters: {self._format_set(operation_params)}",
            f"\t\t\tFrom pipeline configuration: {self._format_pipeline_config(node.processor_config)}",
            f"\t\t\tFrom context: {self._format_set(context_params)}",
            f"\t\tContext additions: {self._format_set(created_keys)}",
        ]

        # Add context suppressions if the node is a ContextNode
        if isinstance(node, ContextNode):
            suppressed_keys = node.processor.get_suppressed_keys()
            deleted_keys.update(suppressed_keys)
            node_summary_lines.append(
                f"\t\tContext suppressions: {self._format_set(suppressed_keys)}"
            )

        return node_summary_lines

    def _validate_deleted_keys(
        self,
        index: int,
        operation_params: set[str],
        config_params: set[str],
        deleted_keys: set[str],
    ) -> None:
        """Raise error if node requires keys previously deleted."""
        missing_deleted_keys = operation_params & deleted_keys
        if not missing_deleted_keys.issubset(config_params):
            raise PipelineConfigurationError(
                f"Node {index} requires context keys previously deleted: {missing_deleted_keys}"
            )

    def _calculate_required_context_keys(
        self,
        all_required_params: set[str],
        injected_or_created_keywords: set[str],
    ) -> set[str]:
        """Calculate which context keys are ultimately needed."""
        return all_required_params - injected_or_created_keywords

    def _format_pipeline_config(self, processor_config: dict[str, Any]) -> str:
        """Format parameters explicitly set in pipeline config."""
        if processor_config:
            return ", ".join(
                f"{key}={value}" for key, value in processor_config.items()
            )
        return "None"

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
        nodes = []
        prev_output_type = None

        for index, node_config in enumerate(self.pipeline_configuration, start=1):
            node = node_factory(node_config, self.logger)
            self.logger.info(f"Initialized Node {index}: {type(node).__name__}")
            nodes.append(node)

            # Skip type consistency check for `ContextNode`
            if isinstance(node, ContextNode):
                continue

            # Perform type consistency check
            input_type = node.input_data_type()
            # Enforce strict type matching otherwise
            if prev_output_type and input_type:
                if prev_output_type != input_type:
                    raise PipelineTopologyError(
                        f"Output of "
                        f"{prev_output_type.__class__.__name__} ({prev_output_type}) "
                        f"not compatible with "
                        f"{node.processor.__class__.__name__} ({input_type})."
                    )

            # if prev_output_type and input_type and prev_output_type != input_type:
            #    raise TypeError(
            #        f"Type mismatch: Expected {prev_output_type} → {input_type} in pipeline."
            #    )

            # Update previous output type for next iteration
            prev_output_type = node.output_data_type()

        print("Nodes: ", nodes)
        return nodes
