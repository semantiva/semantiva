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
from typing import List, Optional, Mapping, Any

from semantiva.pipeline.payload import Payload
from semantiva.trace.model import NodeAddress, NodeTraceEvent, TraceDriver
from semantiva.pipeline.graph_builder import build_graph, compute_pipeline_id
import time
from datetime import datetime
import uuid
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
        trace: TraceDriver | None = None,
        pipeline_spec: List[Mapping[str, Any]] | None = None,
    ) -> Payload:
        """
        Walk the pipeline DAG, process each node, and publish intermediate results.

        Emits before, after, and error events when tracing is enabled.
        Zero overhead when trace is None (no run_id, no canonicalization, no timings).

        Args:
            nodes:     Ordered list of _PipelineNode instances forming the pipeline.
            payload:   Initial payload for the first node.
            transport: Transport for publishing each node's output.
            logger:    Logger for debug/info messages.
            trace:     Optional TraceDriver to emit trace records.
            pipeline_spec: Canonical node specifications when tracing is enabled.

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

    def __init__(self, executor: Optional[SemantivaExecutor] = None):
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
        trace: TraceDriver | None = None,
        pipeline_spec: List[Mapping[str, Any]] | None = None,
    ) -> Payload:
        """
        Execute each node in the provided pipeline in order.

        Emits before, after, and error events when tracing is enabled.
        Zero overhead when trace is None (no run_id, no canonicalization, no timings).

        When ``trace`` is provided, the orchestrator emits ``pipeline_start`` and
        ``pipeline_end`` records along with per-node ``before``/``after`` events.
        No tracing overhead is incurred when ``trace`` is ``None``.

        Args:
            nodes:     List of pipeline nodes to execute sequentially.
            payload:   Input payload for the first node.
            transport: Transport used to publish intermediate outputs.
            logger:    Logger for orchestration debug/info messages.
            trace:     Optional TraceDriver to emit trace records.
            pipeline_spec: Canonical node specifications when tracing is enabled.

        Returns:
            The final (data, context) after all nodes have run.
        """

        data = payload.data
        context = payload.context

        run_id = None
        pipeline_id = None
        node_uuids: List[str] = []
        if trace is not None:
            assert pipeline_spec is not None, "pipeline_spec required when tracing"
            canonical = build_graph(pipeline_spec)
            pipeline_id = compute_pipeline_id(canonical)
            node_uuids = [n["node_uuid"] for n in canonical["nodes"]]
            run_id = f"run-{uuid.uuid4().hex}"
            meta = {"num_nodes": len(node_uuids)}
            # provide optional pipeline input snapshot (backward compatible)
            try:
                trace.on_pipeline_start(
                    pipeline_id, run_id, canonical, meta, pipeline_input=payload
                )
            except TypeError:
                # Older drivers/tests without the new parameter
                trace.on_pipeline_start(pipeline_id, run_id, canonical, meta)

        for index, node in enumerate(nodes, start=1):
            logger.info(f"Running node {index}: {node.processor.__class__.__name__}")
            if trace is not None and run_id and pipeline_id:
                addr = NodeAddress(run_id, pipeline_id, node_uuids[index - 1])
                before = NodeTraceEvent(
                    phase="before",
                    address=addr,
                    params=None,
                    input_payload=None,
                    output_payload=None,
                    error_type=None,
                    error_msg=None,
                    event_time_utc=datetime.utcnow().isoformat(timespec="milliseconds")
                    + "Z",
                    t_wall=None,
                    t_cpu=None,
                )
                trace.on_node_event(before)
                start_wall = time.time()
                start_cpu = time.process_time()

            try:
                payload = node.process(Payload(data, context))
                data, context = payload.data, payload.context
                if trace is not None and run_id and pipeline_id:
                    t_wall = time.time() - start_wall
                    t_cpu = time.process_time() - start_cpu
                    after = NodeTraceEvent(
                        phase="after",
                        address=addr,
                        params=None,
                        input_payload=None,
                        output_payload=Payload(data, context),
                        error_type=None,
                        error_msg=None,
                        event_time_utc=datetime.utcnow().isoformat(
                            timespec="milliseconds"
                        )
                        + "Z",
                        t_wall=t_wall,
                        t_cpu=t_cpu,
                    )
                    trace.on_node_event(after)
            except Exception as exc:
                if trace is not None and run_id and pipeline_id:
                    t_wall = time.time() - start_wall
                    t_cpu = time.process_time() - start_cpu
                    err = NodeTraceEvent(
                        phase="error",
                        address=addr,
                        params=None,
                        input_payload=None,
                        output_payload=None,
                        error_type=type(exc).__name__,
                        error_msg=str(exc),
                        event_time_utc=datetime.utcnow().isoformat(
                            timespec="milliseconds"
                        )
                        + "Z",
                        t_wall=t_wall,
                        t_cpu=t_cpu,
                    )
                    trace.on_node_event(err)
                raise

            transport.publish(
                channel=node.processor.semantic_id(), data=data, context=context
            )

        if trace is not None and run_id:
            trace.on_pipeline_end(run_id, {"status": "ok"})
            trace.flush()
            trace.close()
        return Payload(data, context)
