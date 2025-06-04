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

"""
Defines the SemantivaOrchestrator abstraction and the default local implementation.
The orchestrator is the control-plane component that drives a Semantiva pipeline:
it walks the sequence of PipelineNode instances, invokes their processing logic,
and publishes intermediate results over the configured SemantivaTransport.

This decouples “what to run” (pipeline topology) from “how to run it” (executor)
and “where to send results” (transport), enabling pluggable local, in-memory,
or distributed orchestrators.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

from semantiva.data_types import BaseDataType
from semantiva.context_processors.context_types import ContextType
from semantiva.execution_tools.executor.executor import (
    SemantivaExecutor,
    SequentialSemantivaExecutor,
)
from semantiva.execution_tools.transport import SemantivaTransport
from semantiva.payload_operations.nodes.nodes import PipelineNode
from semantiva.logger import Logger


class SemantivaOrchestrator(ABC):
    """
    Abstract base class for Semantiva orchestrators (control-plane schedulers).

    An orchestrator is responsible for executing a pipeline—a collection of
    PipelineNode objects—in the correct order, using a provided executor,
    and publishing outputs via a transport.

    Subclasses must implement:
        execute(nodes, data, context, transport, logger) -> (data, context)
    """

    @abstractmethod
    def execute(
        self,
        nodes: List[PipelineNode],
        data: BaseDataType,
        context: ContextType,
        transport: SemantivaTransport,
        logger: Logger,
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Walk the pipeline DAG, process each node, and publish intermediate results.

        Args:
            nodes:     Ordered list of PipelineNode instances forming the pipeline.
            data:      Initial data payload (BaseDataType) for the first node.
            context:   Initial context (ContextType) for the first node.
            transport: Transport for publishing each node's output.
            logger:    Logger for debug/info messages.

        Returns:
            A tuple (data, context) after the final node has executed.
        """
        ...


class LocalSemantivaOrchestrator(SemantivaOrchestrator):
    """
    Default local orchestrator that runs pipeline nodes sequentially
    in the current process using a SemantivaExecutor.

    By default, it uses SequentialSemantivaExecutor (synchronous execution),
    but you can inject any SemantivaExecutor (e.g. thread pool, Ray).
    """

    def __init__(self, executor: SemantivaExecutor | None = None):
        """
        Initialize the orchestrator.

        Args:
            executor: Optional SemantivaExecutor instance. If None,
                      uses SequentialSemantivaExecutor for in-thread execution.
        """
        self.executor = executor or SequentialSemantivaExecutor()

    def execute(
        self,
        nodes: List[PipelineNode],
        data: BaseDataType,
        context: ContextType,
        transport: SemantivaTransport,
        logger: Logger,
    ) -> Tuple[BaseDataType, ContextType]:
        """
        Execute each node in the provided pipeline in order.

        For each node:
          1. Log debug information about the node being processed.
          2. Invoke node.process(data, context) to get new (data, context).
          3. Publish the updated (data, context) on the transport,
             using the node's semantic identifier as the subject.

        Args:
            nodes:     List of pipeline nodes to execute sequentially.
            data:      Input data for the first node.
            context:   Input context for the first node.
            transport: Transport used to publish intermediate outputs.
            logger:    Logger for orchestration debug/info messages.

        Returns:
            The final (data, context) after all nodes have run.
        """
        for index, node in enumerate(nodes, start=1):
            # Log which processor is being executed
            logger.debug(
                f"Orchestrator executing node {index}: {node.processor.__class__.__name__}"
            )
            # Run the node’s processing logic (possibly via executor)
            # Note: default implementation ignores executor and calls node.process directly
            data, context = node.process(data, context)

            # Publish intermediate result for this node
            transport.publish(
                channel=node.processor.semantic_id(), data=data, context=context
            )

        # Return the output of the last node
        return data, context
