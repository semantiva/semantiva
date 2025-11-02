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

"""SER enrichment tests for parameter sweep preprocessors."""

from __future__ import annotations

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
    ) -> None:  # pragma: no cover - unused
        return

    def on_run_space_start(self, *args, **kwargs) -> None:  # pragma: no cover - unused
        return

    def on_run_space_end(self, *args, **kwargs) -> None:  # pragma: no cover - unused
        return

    def flush(self) -> None:  # pragma: no cover - unused
        return

    def close(self) -> None:  # pragma: no cover - unused
        return


def _pipeline() -> list[dict[str, object]]:
    return [
        {
            "processor": "FloatMultiplyOperation",
            "derive": {
                "parameter_sweep": {
                    "parameters": {"factor": "3 * t"},
                    "variables": {"t": [1.0, 2.0]},
                    "collection": "FloatDataCollection",
                    "mode": "combinatorial",
                }
            },
        }
    ]


def test_ser_contains_preprocessing_provenance() -> None:
    ProcessorRegistry.register_modules("semantiva.examples.test_utils")
    canonical, resolved = build_canonical_spec(_pipeline())

    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()

    payload = Payload(FloatDataType(1.0), ContextType({}))
    trace = _MemTrace()

    orchestrator.execute(
        pipeline_spec=list(resolved),
        payload=payload,
        transport=transport,
        logger=logger,
        trace=trace,
        canonical_spec=canonical,
    )

    assert trace.pipeline_start is not None
    meta = trace.pipeline_start["meta"]
    assert "config_id" in meta
    assert meta["node_semantic_ids"], "node_semantic_ids should not be empty"

    assert trace.records, "SER records were not captured"
    processor = trace.records[0].processor
    assert "semantic_id" in processor
    provenance = processor.get("preprocessing_provenance")
    assert isinstance(provenance, dict)
    assert provenance.get("type") == "derive.parameter_sweep"

    node_uuid, semantic_id = next(iter(meta["node_semantic_ids"].items()))
    assert semantic_id == processor["semantic_id"]
