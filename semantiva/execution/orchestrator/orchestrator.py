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
from typing import List, Optional, Any

from semantiva.pipeline.payload import Payload
from semantiva.trace.model import IODelta, SERRecord, TraceDriver
from semantiva.trace._utils import (
    serialize,
    sha256_bytes,
    safe_repr,
    canonical_json_bytes,
    context_to_kv_repr,
)
from semantiva.pipeline.graph_builder import (
    build_canonical_spec,
    compute_pipeline_id,
    compute_upstream_map,
)
import time
from datetime import datetime
import uuid
from semantiva.execution.executor.executor import (
    SemantivaExecutor,
    SequentialSemantivaExecutor,
)
from semantiva.execution.transport import SemantivaTransport
from semantiva.pipeline.nodes.nodes import _PipelineNode
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.registry.descriptors import instantiate_from_descriptor
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

    _last_nodes: List[_PipelineNode] = []

    @property
    def last_nodes(self) -> List[_PipelineNode]:
        return self._last_nodes

    @abstractmethod
    def execute(
        self,
        pipeline_spec: List[dict[str, Any]],
        payload: Payload,
        transport: SemantivaTransport,
        logger: Logger,
        trace: TraceDriver | None = None,
        canonical_spec: dict[str, Any] | None = None,
    ) -> Payload:
        """
        Walk the pipeline DAG, process each node, and publish intermediate results.

        Emits before, after, and error events when tracing is enabled.
        Zero overhead when trace is None (no run_id, no canonicalization, no timings).

        Args:
            pipeline_spec: Resolved node configurations with descriptors.
            payload:   Initial payload for the first node.
            transport: Transport for publishing each node's output.
            logger:    Logger for debug/info messages.
            trace:     Optional TraceDriver to emit trace records.
            canonical_spec: Optional precomputed canonical spec for tracing.

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
        self._last_nodes: List[_PipelineNode] = []

    @property
    def last_nodes(self) -> List[_PipelineNode]:
        return self._last_nodes

    def execute(
        self,
        pipeline_spec: List[dict[str, Any]],
        payload: Payload,
        transport: SemantivaTransport,
        logger: Logger,
        trace: TraceDriver | None = None,
        canonical_spec: dict[str, Any] | None = None,
    ) -> Payload:
        """
        Execute each node in the provided pipeline in order.

        Emits before, after, and error events when tracing is enabled.
        Zero overhead when trace is None (no run_id, no canonicalization, no timings).

        When ``trace`` is provided, the orchestrator emits ``pipeline_start`` and
        ``pipeline_end`` records along with per-node ``before``/``after``/``error`` events.
        Error events capture timing data and exception details for failed nodes.
        Trace resources (flush/close) are properly managed even when execution fails.
        No tracing overhead is incurred when ``trace`` is ``None``.

        Args:
            pipeline_spec: List of node configs with descriptors.
            payload:   Input payload for the first node.
            transport: Transport used to publish intermediate outputs.
            logger:    Logger for orchestration debug/info messages.
            trace:     Optional TraceDriver to emit trace records.
            canonical_spec: Optional precomputed canonical spec.

        Returns:
            The final (data, context) after all nodes have run.
        """

        data = payload.data
        context = payload.context

        canonical = canonical_spec
        if canonical is None:
            canonical, pipeline_spec = build_canonical_spec(pipeline_spec)

        run_id = None
        pipeline_id = None
        node_uuids: List[str] = []
        upstream_map: dict[str, list[str]] = {}
        trace_opts = {"hash": False, "repr": False, "context": False}
        if trace is not None:
            pipeline_id = compute_pipeline_id(canonical)
            node_uuids = [n["node_uuid"] for n in canonical["nodes"]]
            upstream_map = compute_upstream_map(canonical)
            run_id = f"run-{uuid.uuid4().hex}"
            meta = {"num_nodes": len(node_uuids)}
            try:
                trace.on_pipeline_start(
                    pipeline_id, run_id, canonical, meta, pipeline_input=payload
                )
            except TypeError:
                trace.on_pipeline_start(pipeline_id, run_id, canonical, meta)
            trace_opts = getattr(trace, "get_options", lambda: {"hash": True})()

        nodes: List[_PipelineNode] = []
        for node_def in pipeline_spec:
            params = instantiate_from_descriptor(node_def.get("parameters", {}))
            nd = dict(node_def)
            nd["parameters"] = params
            node = _pipeline_node_factory(nd, logger)
            nodes.append(node)

        self._last_nodes = nodes

        try:
            for index, node in enumerate(nodes, start=1):
                logger.info(
                    f"Running node {index}: {node.processor.__class__.__name__}"
                )
                if trace is not None and run_id and pipeline_id:
                    start_wall = time.time()
                    start_cpu = time.process_time()
                    start_iso = datetime.now().isoformat(timespec="milliseconds") + "Z"
                    summaries: dict[str, dict[str, object]] = {}
                    if trace_opts.get("hash") or trace_opts.get("repr"):
                        inp: dict[str, object] = {"dtype": type(data).__name__}
                        try:
                            inp["rows"] = len(data)  # type: ignore[arg-type]
                        except Exception:
                            pass
                        if trace_opts.get("hash"):
                            inp["sha256"] = sha256_bytes(serialize(data))
                        if trace_opts.get("repr"):
                            inp["repr"] = safe_repr(data)
                        summaries["input_data"] = inp
                        pre_ctx = (
                            context.to_dict() if hasattr(context, "to_dict") else {}
                        )
                        pre_ctx_summary: dict[str, object] = {}
                        if trace_opts.get("hash"):
                            pre_ctx_summary["sha256"] = sha256_bytes(
                                canonical_json_bytes(pre_ctx)
                            )
                        if trace_opts.get("repr") and trace_opts.get("context"):
                            pre_ctx_summary["repr"] = context_to_kv_repr(pre_ctx)
                        if pre_ctx_summary:
                            summaries["pre_context"] = pre_ctx_summary

                try:
                    payload = node.process(Payload(data, context))
                    data, context = payload.data, payload.context
                    if trace is not None and run_id and pipeline_id:
                        t_wall = time.time() - start_wall
                        cpu_ms = int((time.process_time() - start_cpu) * 1000)
                        end_iso = (
                            datetime.now().isoformat(timespec="milliseconds") + "Z"
                        )
                        if trace_opts.get("hash") or trace_opts.get("repr"):
                            out: dict[str, object] = {"dtype": type(data).__name__}
                            try:
                                out["rows"] = len(data)  # type: ignore[arg-type]
                            except Exception:
                                pass
                            if trace_opts.get("hash"):
                                out["sha256"] = sha256_bytes(serialize(data))
                            if trace_opts.get("repr"):
                                out["repr"] = safe_repr(data)
                            summaries["output_data"] = out
                            post_ctx = (
                                payload.context.to_dict()
                                if hasattr(payload.context, "to_dict")
                                else {}
                            )
                            post_ctx_summary: dict[str, object] = {}
                            if trace_opts.get("hash"):
                                post_ctx_summary["sha256"] = sha256_bytes(
                                    canonical_json_bytes(post_ctx)
                                )
                            if trace_opts.get("repr") and trace_opts.get("context"):
                                post_ctx_summary["repr"] = context_to_kv_repr(post_ctx)
                            if post_ctx_summary:
                                summaries["post_context"] = post_ctx_summary

                        ser = SERRecord(
                            type="ser",
                            schema_version=2,
                            ids={
                                "run_id": run_id,
                                "pipeline_id": pipeline_id,
                                "node_id": node_uuids[index - 1],
                            },
                            topology={
                                "upstream": upstream_map.get(node_uuids[index - 1], [])
                            },
                            action={
                                "op_ref": node.processor.__class__.__name__,
                                "params": {},
                                "param_source": {},
                            },
                            io_delta=IODelta(
                                [], [], [], {}
                            ),  # TODO: populate read/write sets
                            checks={
                                "why_run": {
                                    "trigger": "dependency",
                                    "upstream_evidence": [],
                                    "pre": [],
                                    "policy": [],
                                },
                                "why_ok": {
                                    "post": [],
                                    "invariants": [],
                                    "env": {},
                                    "redaction": {},
                                },
                            },
                            timing={
                                "start": start_iso,
                                "end": end_iso,
                                "duration_ms": int(t_wall * 1000),
                                "cpu_ms": cpu_ms,
                            },
                            status="completed",
                            labels={"node_fqn": node.processor.__class__.__name__},
                            summaries=summaries or None,
                        )
                        trace.on_node_event(ser)
                except Exception as exc:
                    if trace is not None and run_id and pipeline_id:
                        t_wall = time.time() - start_wall
                        cpu_ms = int((time.process_time() - start_cpu) * 1000)
                        end_iso = (
                            datetime.now().isoformat(timespec="milliseconds") + "Z"
                        )
                        err_summary = summaries or {}
                        ser = SERRecord(
                            type="ser",
                            schema_version=2,
                            ids={
                                "run_id": run_id,
                                "pipeline_id": pipeline_id,
                                "node_id": node_uuids[index - 1],
                            },
                            topology={
                                "upstream": upstream_map.get(node_uuids[index - 1], [])
                            },
                            action={
                                "op_ref": node.processor.__class__.__name__,
                                "params": {},
                                "param_source": {},
                            },
                            io_delta=IODelta(
                                [], [], [], {}
                            ),  # TODO: populate read/write sets
                            checks={
                                "why_run": {
                                    "trigger": "dependency",
                                    "upstream_evidence": [],
                                    "pre": [],
                                    "policy": [],
                                },
                                "why_ok": {
                                    "post": [
                                        {
                                            "code": type(exc).__name__,
                                            "result": "FAIL",
                                            "details": {"error": str(exc)},
                                        }
                                    ],
                                    "invariants": [],
                                    "env": {},
                                    "redaction": {},
                                },
                            },
                            timing={
                                "start": start_iso,
                                "end": end_iso,
                                "duration_ms": int(t_wall * 1000),
                                "cpu_ms": cpu_ms,
                            },
                            status="error",
                            error={"type": type(exc).__name__, "message": str(exc)},
                            labels={"node_fqn": node.processor.__class__.__name__},
                            summaries=err_summary or None,
                        )
                        trace.on_node_event(ser)
                    raise

                transport.publish(
                    channel=node.processor.semantic_id(), data=data, context=context
                )

            if trace is not None and run_id:
                trace.on_pipeline_end(run_id, {"status": "ok"})
        except Exception as exc:
            # Ensure trace is properly closed even on error
            if trace is not None and run_id:
                trace.on_pipeline_end(run_id, {"status": "error", "error": str(exc)})
                trace.flush()
                trace.close()
            raise
        else:
            # Normal completion path
            if trace is not None and run_id:
                trace.flush()
                trace.close()

        return Payload(data, context)
