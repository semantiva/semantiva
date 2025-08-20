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

from typing import Any, Dict, List, Optional
from .payload import Payload
from semantiva.logger import Logger
from .payload_processors import _PayloadProcessor
from .nodes._pipeline_node_factory import _pipeline_node_factory
from .nodes.nodes import (
    _PipelineNode,
    _ProbeResultCollectorNode,
)
from semantiva.execution.transport import (
    SemantivaTransport,
    InMemorySemantivaTransport,
)
from semantiva.execution.orchestrator.orchestrator import (
    SemantivaOrchestrator,
    LocalSemantivaOrchestrator,
)


class Pipeline(_PayloadProcessor):
    """A class for orchestrating multiple payload operations by sequentially processing data and context."""

    pipeline_configuration: List[Dict]
    nodes: List[_PipelineNode]

    def __init__(
        self,
        pipeline_configuration: List[Dict],
        logger: Optional[Logger] = None,
        transport: Optional[SemantivaTransport] = None,
        orchestrator: Optional[SemantivaOrchestrator] = None,
    ):
        """
        Initializes the pipeline with the given configuration, logger, transport, and orchestrator.
        Args:
            pipeline_configuration (List[Dict]): A list of dictionaries containing the pipeline configuration.
            logger (Optional[Logger], optional): An optional logger instance for logging information. Defaults to None.
            transport (Optional[SemantivaTransport], optional): An optional transport mechanism for the pipeline.
                If not provided, an InMemorySemantivaTransport instance will be used. Defaults to None.
            orchestrator (Optional[SemantivaOrchestrator], optional): An optional orchestrator for managing pipeline execution.
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

        # Use inspection system for validation
        from semantiva.inspection import build_pipeline_inspection, validate_pipeline

        inspection = build_pipeline_inspection(pipeline_configuration)
        validate_pipeline(inspection)  # This will raise if there are any errors

        self.nodes = self._initialize_nodes()  # existing initialization logic
        if self.logger:
            self.logger.debug(f"Initialized {self.__class__.__name__}")

    def _process(self, payload: Payload) -> Payload:
        """
        Processes the pipeline by executing the orchestrator with the provided data and context.
        This method starts a stopwatch timer to measure the execution time of the pipeline,
        logs the start and completion of the pipeline processing, and provides a detailed
        timing report upon completion.
        Args:
            payload (Payload): Input payload for the pipeline.
        Returns:
            Payload: The processed payload after all nodes are executed.
        Logs:
            - Info: Logs the start and completion of the pipeline processing.
            - Debug: Logs a detailed timing report of the pipeline execution.
        """
        self.logger.debug("Start processing pipeline")
        self.stop_watch.start()  # existing pipeline timer start

        result_payload = self.orchestrator.execute(
            nodes=self.nodes,
            payload=payload,
            transport=self.transport,
            logger=self.logger,
        )

        self.stop_watch.stop()  # existing pipeline timer stop
        self.logger.debug("Pipeline execution complete.")
        self.logger.debug(
            "Pipeline execution timing report: \n\tPipeline %s\n%s",
            str(self.stop_watch),
            self.get_timers(),
        )
        return result_payload

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
        `_ProbeResultCollectorNode`. For each such node, it retrieves the collected data and
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

            if isinstance(node, _ProbeResultCollectorNode):
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

        This method uses the `_pipeline_node_factory` function to create nodes from the provided
        pipeline configuration. Each node is then added to the pipeline.

        Note: Validation is now handled by the inspection system before this method is called.
        """
        nodes = []

        for index, node_config in enumerate(self.pipeline_configuration, start=1):
            node = _pipeline_node_factory(node_config, self.logger)
            self.logger.debug(f"Initialized Node {index}: {type(node).__name__}")
            nodes.append(node)

        return nodes

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:

        # Define the metadata for the Pipeline class
        component_metadata = {
            "component_type": "Pipeline",
        }
        return component_metadata
