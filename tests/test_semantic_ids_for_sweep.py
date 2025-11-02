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

"""Tests for semantic identity fingerprints on parameter sweeps."""

from __future__ import annotations

import pytest

from semantiva.context_processors.context_types import ContextType
from semantiva.examples.test_utils import FloatDataType
from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.logger import Logger
from semantiva.pipeline.graph_builder import build_canonical_spec
from semantiva.pipeline.payload import Payload
from semantiva.registry.processor_registry import ProcessorRegistry
from semantiva.trace.model import SERRecord, TraceDriver


class _MemTrace(TraceDriver):
    """In-memory trace driver capturing pipeline start metadata and SER records."""

    def __init__(self) -> None:
        self.pipeline_start: dict | None = None
        self.records: list[SERRecord] = []

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        pipeline_spec_canonical: dict,
        meta: dict,
        pipeline_input=None,
        **kwargs,
    ) -> None:
        self.pipeline_start = {
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "meta": dict(meta),
        }

    def on_node_event(self, event: SERRecord) -> None:
        self.records.append(event)

    def on_pipeline_end(
        self, run_id: str, summary: dict
    ) -> None:  # pragma: no cover - not used
        return

    def on_run_space_start(self, *args, **kwargs) -> None:  # pragma: no cover - unused
        return

    def on_run_space_end(self, *args, **kwargs) -> None:  # pragma: no cover - unused
        return

    def flush(self) -> None:  # pragma: no cover - unused
        return

    def close(self) -> None:  # pragma: no cover - unused
        return


def _pipeline(expr: str) -> list[dict[str, object]]:
    return [
        {
            "processor": "FloatMultiplyOperation",
            "derive": {
                "parameter_sweep": {
                    "parameters": {"factor": expr},
                    "variables": {"t": [1.0, 2.0, 3.0]},
                    "collection": "FloatDataCollection",
                    "mode": "combinatorial",
                }
            },
        }
    ]


@pytest.mark.parametrize(
    ("expr_a", "expr_b", "should_equal"),
    [
        ("3 * t", "t * 3", True),
        ("2 * (t + 5)", "(5 + t) * 2", True),
        ("3.0 * t", "3.1 * t", False),
        ("t + 1", "t + 2", False),
    ],
)
def test_pipeline_config_id_semantics(
    expr_a: str, expr_b: str, should_equal: bool
) -> None:
    ProcessorRegistry.register_modules("semantiva.examples.test_utils")
    canonical_a, resolved_a = build_canonical_spec(_pipeline(expr_a))
    canonical_b, resolved_b = build_canonical_spec(_pipeline(expr_b))

    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()

    payload_a = Payload(FloatDataType(1.0), ContextType({}))
    payload_b = Payload(FloatDataType(1.0), ContextType({}))

    trace_a = _MemTrace()
    trace_b = _MemTrace()

    orchestrator.execute(
        pipeline_spec=list(resolved_a),
        payload=payload_a,
        transport=transport,
        logger=logger,
        trace=trace_a,
        canonical_spec=canonical_a,
    )
    orchestrator.execute(
        pipeline_spec=list(resolved_b),
        payload=payload_b,
        transport=transport,
        logger=logger,
        trace=trace_b,
        canonical_spec=canonical_b,
    )

    plc_a = (
        trace_a.pipeline_start["meta"].get("config_id")
        if trace_a.pipeline_start
        else None
    )
    plc_b = (
        trace_b.pipeline_start["meta"].get("config_id")
        if trace_b.pipeline_start
        else None
    )
    assert plc_a and plc_b
    if should_equal:
        assert plc_a == plc_b
    else:
        assert plc_a != plc_b
