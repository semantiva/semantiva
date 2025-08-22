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

"""Trace model for Semantiva (v1).

Defines stable types used by tracing:
  - NodeAddress: (pipeline_run_id, pipeline_id, node_uuid)
  - NodeTraceEvent: Trace "node" envelope payload (phase, timings, error, etc.)
  - TraceDriver: driver protocol; Requires on_pipeline_start/node_event/pipeline_end, flush, close.

Notes:
  • V1 consumers must switch on "type" and ignore unknown fields.
  • Reserved ODO fields: plan_id (None), plan_epoch (0).
  • Orchestrator may pass pipeline_input to on_pipeline_start (optional, drivers MAY ignore).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Literal, Optional

from semantiva.pipeline.payload import Payload


@dataclass(frozen=True)
class NodeAddress:
    """Stable address for a node event.

    Attributes:
      pipeline_run_id: Unique run identifier (e.g., "run-<uuidv7/hex>").
      pipeline_id: Deterministic hash of canonical GraphV1 ("plid-<sha256>").
      node_uuid: Deterministic UUIDv5 derived from the node's canonical definition.
    """

    pipeline_run_id: str
    pipeline_id: str
    node_uuid: str


@dataclass(frozen=True)
class NodeTraceEvent:
    """Node event payload (v1).

    Fields mirror "node" record:
      phase: "before" | "after" | "error".
      address: NodeAddress triple.
      params: Optional shallow mapping of node parameters (or None).
      input_payload / output_payload: Optional payload snapshots (drivers may summarize).
      error_type / error_msg: Populated on "error", else None.
      event_time_utc: ISO8601 Zulu with millisecond precision.
      t_wall / t_cpu: Wall/CPU seconds; None on "before".
      plan_id / plan_epoch: Reserved for ODO; v1 sets None/0.

    Notes:
      • Drivers may add summaries (hashes, reprs); consumers must ignore unknown fields.
      • Orchestrator sets input/output payload to None for v1 minimal cost.
    """

    phase: Literal["before", "after", "error"]
    address: NodeAddress
    params: Mapping[str, Any] | None
    input_payload: Payload | None
    output_payload: Payload | None
    error_type: str | None
    error_msg: str | None
    event_time_utc: str
    t_wall: float | None
    t_cpu: float | None
    plan_id: str | None = None
    plan_epoch: int = 0
    # Optional output-only summaries (populated by driver, output phase only)
    out_data_repr: str | None = None
    out_data_hash: str | None = None
    post_context_hash: str | None = None


class TraceDriver(Protocol):
    """Driver API for Semantiva tracing (v1).

    Implementations should be resilient to extra fields and ignore unknown kwargs.
    """

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input: Optional[Payload] = None,
    ) -> None:
        """Emit a trace "pipeline_start" record.

        Args:
          pipeline_id: "plid-<sha256>" for the canonical GraphV1.
          run_id: Unique run identifier for this execution.
          canonical_spec: Canonical GraphV1 ({"version": 1, "nodes": [...], "edges": [...]}).
          meta: Minimal run metadata (e.g., {"num_nodes": int}).
          pipeline_input: Optional payload snapshot (drivers MAY ignore).

        Notes:
          • This optional parameter extends the Epic's minimal interface.
            Orchestrator passes it when available; drivers without this parameter
            remain runtime-compatible (the orchestrator catches TypeError).
          • Consumers should NOT rely on snapshots; Trace v1 guarantees are in the envelopes.
        """
        ...

    def on_node_event(self, event: NodeTraceEvent) -> None: ...

    def on_pipeline_end(self, run_id: str, summary: dict) -> None: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...
