# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from typing import Any, Dict, List, Optional, Tuple
from semantiva.exceptions.pipeline import (
    PipelineTopologyError,
)
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import BaseDataType
from semantiva.logger import Logger
from .pipeline_inspector import PipelineInspector
from .payload_processors import PayloadProcessor
from .nodes.node_factory import node_factory
from .nodes.nodes import (
    PipelineNode,
    ContextProcessorNode,
    ProbeResultCollectorNode,
)
from semantiva.execution_tools.transport import (
    SemantivaTransport,
    InMemorySemantivaTransport,
)
from semantiva.execution_tools.orchestrator.orchestrator import (
    SemantivaOrchestrator,
    LocalSemantivaOrchestrator,
)


class Pipeline(PayloadProcessor):
    """A class for orchestrating multiple payload operations by sequentially processing data and context."""

    pipeline_configuration: List[Dict]
    nodes: List[PipelineNode]

    def __init__(
        self,
        pipeline_configuration: List[Dict],
        logger: Logger | None = None,
        transport: SemantivaTransport | None = None,
        orchestrator: SemantivaOrchestrator | None = None,
    ):
        """
        Initializes the pipeline with the given configuration, logger, transport, and orchestrator.
        Args:
            pipeline_configuration (List[Dict]): A list of dictionaries containing the pipeline configuration.
            logger (Logger | None, optional): An optional logger instance for logging information. Defaults to None.
            transport (SemantivaTransport | None, optional): An optional transport mechanism for the pipeline.
                If not provided, an InMemorySemantivaTransport instance will be used. Defaults to None.
            orchestrator (SemantivaOrchestrator | None, optional): An optional orchestrator for managing pipeline execution.
                If not provided, a LocalSemantivaOrchestrator instance will be used. Defaults to None.
        Attributes:
            pipeline_configuration (List[Dict]): Stores the pipeline configuration.
            transport (SemantivaTransport): The transport mechanism used by the pipeline.
            orchestrator (SemantivaOrchestrator): The orchestrator managing the pipeline execution.
            nodes (List): The initialized nodes of the pipeline.
        """

        super().__init__(logger)
        self.pipeline_configuration = pipeline_configuration
        self.transport = transport or InMemorySemantivaTransport()
        self.orchestrator = orchestrator or LocalSemantivaOrchestrator()
        self.nodes = self._initialize_nodes()  # existing initialization logic
        if self.logger:
            self.logger.info(f"Initialized {self.__class__.__name__}")
            self.logger.debug("%s", self.inspect())

    def _process(
        self, data: BaseDataType, context: ContextType
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Processes the pipeline by executing the orchestrator with the provided data and context.
        This method starts a stopwatch timer to measure the execution time of the pipeline,
        logs the start and completion of the pipeline processing, and provides a detailed
        timing report upon completion.
        Args:
            data (BaseDataType): The input data to be processed by the pipeline.
            context (ContextType): The context information required for processing.
        Returns:
            Tuple[BaseDataType, ContextType]: A tuple containing the processed data and the updated context.
        Logs:
            - Info: Logs the start and completion of the pipeline processing.
            - Debug: Logs a detailed timing report of the pipeline execution.
        """
        self.logger.info("Start processing pipeline")
        self.stop_watch.start()  # existing pipeline timer start

        result_data, result_context = self.orchestrator.execute(
            nodes=self.nodes,
            data=data,
            context=context,
            transport=self.transport,
            logger=self.logger,
        )

        self.stop_watch.stop()  # existing pipeline timer stop
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
        return PipelineInspector.inspect(self.nodes)

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

            if isinstance(node, ProbeResultCollectorNode):
                # Add the collected data from the node to the results dictionary
                assert hasattr(node, "get_collected_data")
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

            # Skip type consistency check for `ContextProcessorNode`
            if isinstance(node, ContextProcessorNode):
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

            # Update previous output type for next iteration
            prev_output_type = node.output_data_type()

        return nodes

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:

        # Define the metadata for the Pipeline class
        component_metadata = {
            "component_type": "Pipeline",
        }
        return component_metadata

    def _print_nodes_semantic_ids(self):
        """
        Print the semantic ID of each node in the pipeline.

        This method is used for debugging purposes to print the semantic ID of each node
        in the pipeline.
        """

        print("Pipeline inspection:")
        print(self.inspect())
        print()
        for index, node in enumerate(self.nodes, start=1):
            print(f"\nNode {index}")
            print(node.semantic_id())

    def extended_inspection(self) -> str:
        """
        Provides a highly verbose and detailed pipeline inspection, suitable for advanced
        debugging and LLM-based introspection. Each node includes detailed descriptions,
        docstrings (provided as footnotes), parameter sources, and context operations.

        Returns:
            str: An extended inspection report of the pipeline.
        """
        summary_lines = ["Extended Pipeline Inspection:"]
        footnotes: Dict[str, str] = {}

        for index, node in enumerate(self.nodes, start=1):
            injected_keys = set()
            required_context_keys: set[str] = set()
            created_context_keys: set[str] = set()
            metadata = node.get_metadata()
            processor = node.processor
            node_class_name = node.__class__.__name__
            processor_class_name = processor.__class__.__name__

            required_keys = set()
            if hasattr(processor, "get_required_context_keys"):
                required_keys = set(processor.get_required_context_keys())
            required_context_keys.update(required_keys)

            if hasattr(processor, "get_required_keys"):
                required_keys = set(processor.get_required_keys())
                required_context_keys.update(required_keys)

            suppressed_keys = set()
            if hasattr(processor, "get_suppressed_keys"):
                suppressed_keys = set(processor.get_suppressed_keys())

            created_keys = set()
            if hasattr(processor, "get_created_keys"):
                created_keys = set(processor.get_created_keys())
                created_context_keys.update(created_keys)

            if metadata.get("component_type") == "ProbeContextInjectorNode":
                injected_key = getattr(node, "context_keyword", None)
                if injected_key:
                    injected_keys = {injected_key}
                    created_context_keys.add(injected_key)

            processor_config = node.processor_config
            config_params_str = (
                ", ".join(f"{k}={v}" for k, v in processor_config.items())
                if processor_config
                else "None"
            )

            # Prepare detailed node summary
            summary_lines.extend(
                [
                    f"\nNode {index}: {processor_class_name} ({node_class_name})",
                    f"    - Component type: {metadata.get('component_type')}",
                    f"    - Input data type: {node.input_data_type().__name__ if hasattr(node, 'input_data_type') else 'None'}",
                    f"    - Output data type: {node.output_data_type().__name__ if hasattr(node, 'output_data_type') else 'None'}",
                    f"    - Parameters from pipeline configuration: {config_params_str}",
                    f"    - Parameters from context: {', '.join(required_keys) if required_keys else 'None'}",
                    f"    - Context additions: {', '.join(created_keys | injected_keys ) or 'None'}",
                    f"    - Context suppressions: {', '.join(suppressed_keys) if suppressed_keys else 'None'}",
                ]
            )

            # Add detailed descriptions to footnotes
            footnote_key = f"{processor_class_name}"
            if footnote_key not in footnotes:
                processor_doc = (
                    inspect.getdoc(processor.__class__) or "No description provided."
                )
                footnotes[footnote_key] = processor_doc

        required_final_keys = required_context_keys - created_context_keys
        summary_lines.insert(
            1,
            f"    Required context keys: {', '.join(sorted(required_final_keys)) or 'None'}",
        )

        # Append footnotes
        summary_lines.append("\nFootnotes:")
        for name, doc in footnotes.items():
            summary_lines.extend([f"[{name}]", f"{doc}", ""])

        return "\n".join(summary_lines)
