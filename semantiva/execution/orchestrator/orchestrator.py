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
it walks the sequence of _PipelineNode instances, invokes their processing logic,
and publishes intermediate results over the configured SemantivaTransport.

This decouples “what to run” (pipeline topology) from “how to run it” (executor)
and “where to send results” (transport), enabling pluggable local, in-memory,
or distributed orchestrators.
"""

from abc import ABC, abstractmethod
from typing import List

from semantiva.pipeline.payload import Payload
from semantiva.execution.executor.executor import (
    SemantivaExecutor,
    SequentialSemantivaExecutor,
)
from semantiva.execution.transport import SemantivaTransport
from semantiva.pipeline.nodes.nodes import _PipelineNode
from semantiva.logger import Logger


class SemantivaOrchestrator(ABC):
    """
    Abstract base class for Semantiva orchestrators (control-plane schedulers).

    An orchestrator is responsible for executing a pipeline—a collection of
    _PipelineNode objects—in the correct order, using a provided executor,
    and publishing outputs via a transport.

    Subclasses must implement:
        execute(nodes, data, context, transport, logger) -> (data, context)
    """

    @abstractmethod
    def execute(
        self,
        nodes: List[_PipelineNode],
        payload: Payload,
        transport: SemantivaTransport,
        logger: Logger,
    ) -> Payload:
        """
        Walk the pipeline DAG, process each node, and publish intermediate results.

        Args:
            nodes:     Ordered list of _PipelineNode instances forming the pipeline.
            payload:   Initial payload for the first node.
            transport: Transport for publishing each node's output.
            logger:    Logger for debug/info messages.

        Returns:
            Payload after the final node has executed.
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
        nodes: List[_PipelineNode],
        payload: Payload,
        transport: SemantivaTransport,
        logger: Logger,
    ) -> Payload:
        """
        Execute each node in the provided pipeline in order.

        For each node:
          1. Log debug information about the node being processed.
          2. Invoke node.process(data, context) to get new (data, context).
          3. Publish the updated (data, context) on the transport,
             using the node's semantic identifier as the subject.

        Args:
            nodes:     List of pipeline nodes to execute sequentially.
            payload:   Input payload for the first node.
            transport: Transport used to publish intermediate outputs.
            logger:    Logger for orchestration debug/info messages.

        Returns:
            The final (data, context) after all nodes have run.
        """
        data = payload.data
        context = payload.context
        for index, node in enumerate(nodes, start=1):
            # Log which processor is being executed
            logger.debug(
                f"Orchestrator executing node {index}: {node.processor.__class__.__name__}"
            )
            # Run the node’s processing logic (possibly via executor)
            # Note: default implementation ignores executor and calls node.process directly
            payload = node.process(Payload(data, context))
            data, context = payload.data, payload.context

            # Publish intermediate result for this node
            transport.publish(
                channel=node.processor.semantic_id(), data=data, context=context
            )

        # Return the output of the last node
        return Payload(data, context)
