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
Unit tests for Semantiva's LocalSemantivaOrchestrator.

These tests verify that:
  - The orchestrator executes each _PipelineNode in sequence,
  - Uses the default SequentialSemantivaExecutor,
  - Publishes each node's output via the provided transport,
  - Returns the correct final data and context.

This ensures the core, single-process orchestrator behaves as expected
before plugging in more advanced transports or executors.
"""

import pytest

from semantiva.execution.orchestrator.orchestrator import (
    LocalSemantivaOrchestrator,
    SemantivaOrchestrator,
)
from semantiva import Pipeline, Payload
from semantiva.execution.transport import InMemorySemantivaTransport
from semantiva.context_processors.context_types import ContextType
from semantiva.examples.test_utils import FloatDataType, FloatMultiplyOperation
from semantiva.logger import Logger
from semantiva.execution.executor import SequentialSemantivaExecutor
from semantiva.trace.model import TraceDriver, SERRecord


@pytest.fixture
def fake_pipeline():
    """
    Creates a minimal Pipeline instance for testing:
      - Two consecutive FloatMultiplyOperation nodes, each doubling the input.
    Returns:
        Pipeline object with .nodes list populated.
    """
    # We use an in-memory transport and sequential executor just to satisfy
    # _PipelineNode requirements, though they aren't used by LocalSemantivaOrchestrator directly here.

    node_configurations = [
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
    ]

    pipeline = Pipeline(node_configurations)
    return pipeline


def test_orchestrator_applies_each_node_and_publishes(fake_pipeline):
    """
    Verify that LocalSemantivaOrchestrator.execute:
      - Runs each node in order (2.0 → *2 → *2 = 8.0),
      - Returns a FloatDataType with the correct value,
      - Passes the same ContextType instance through unchanged.
    """
    orch = LocalSemantivaOrchestrator()

    # Prepare initial data and context
    initial = FloatDataType(2.0)
    ctx = ContextType({})

    # Execute the pipeline:
    # - fake_pipeline.nodes: list of _PipelineNode
    # - initial: BaseDataType
    # - ctx: ContextType
    # - transport: in-memory transport captures published intermediates
    # - Logger(): dummy logger for debugging internal steps
    payload_output = orch.execute(
        fake_pipeline.resolved_spec,
        Payload(initial, ctx),
        InMemorySemantivaTransport(),
        Logger(),
        canonical_spec=fake_pipeline.canonical_spec,
    )
    data_output, context_output = payload_output.data, payload_output.context

    # After two sequential multiplications by 2, 2.0 → 4.0 → 8.0
    assert data_output.data == 8.0
    # The return type should still be our FloatDataType wrapper
    assert isinstance(data_output, FloatDataType)
    # Context is passed through unchanged
    assert context_output == ctx


def test_orchestrator_uses_executor(monkeypatch, fake_pipeline) -> None:
    calls: list = []
    original = SequentialSemantivaExecutor.submit

    def capture(self, fn, *args, **kwargs):
        calls.append(kwargs.get("ser_hooks"))
        return original(self, fn, *args, **kwargs)

    monkeypatch.setattr(SequentialSemantivaExecutor, "submit", capture)
    orch = LocalSemantivaOrchestrator()
    initial = FloatDataType(1.0)
    ctx = ContextType({})
    orch.execute(
        fake_pipeline.resolved_spec,
        Payload(initial, ctx),
        InMemorySemantivaTransport(),
        Logger(),
        canonical_spec=fake_pipeline.canonical_spec,
    )
    assert len(calls) == len(fake_pipeline.resolved_spec)
    assert all(h is not None for h in calls)


class _CaptureTraceDriver(TraceDriver):
    def __init__(self) -> None:
        self.start: tuple[str, str] | None = None
        self.end: tuple[str, dict] | None = None
        self.events: list[SERRecord] = []

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input=None,
    ) -> None:
        self.start = (pipeline_id, run_id)

    def on_node_event(self, event: SERRecord) -> None:
        self.events.append(event)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        self.end = (run_id, summary)

    def flush(self) -> None: ...

    def close(self) -> None: ...


class RemoteStubOrchestrator(SemantivaOrchestrator):
    def __init__(self) -> None:
        super().__init__()
        self.published: list[tuple[str, object]] = []

    def _submit_and_wait(
        self,
        node_callable,
        *,
        ser_hooks,
    ) -> Payload:
        return node_callable()

    def _publish(self, node, data, context, transport) -> None:
        self.published.append((node.processor.semantic_id(), data))


def test_remote_stub_inherits_template(fake_pipeline):
    tracer_remote = _CaptureTraceDriver()
    tracer_local = _CaptureTraceDriver()
    transport = InMemorySemantivaTransport()
    stub = RemoteStubOrchestrator()
    local = LocalSemantivaOrchestrator()

    payload_remote = Payload(FloatDataType(3.0), ContextType({}))
    payload_local = Payload(FloatDataType(3.0), ContextType({}))

    result_remote = stub.execute(
        fake_pipeline.resolved_spec,
        payload_remote,
        transport,
        Logger(),
        trace=tracer_remote,
        canonical_spec=fake_pipeline.canonical_spec,
    )

    result_local = local.execute(
        fake_pipeline.resolved_spec,
        payload_local,
        InMemorySemantivaTransport(),
        Logger(),
        trace=tracer_local,
        canonical_spec=fake_pipeline.canonical_spec,
    )

    assert isinstance(result_remote.data, FloatDataType)
    assert result_remote.data.data == result_local.data.data
    assert tracer_remote.events and tracer_local.events
    assert len(tracer_remote.events) == len(tracer_local.events)
    remote_ser = tracer_remote.events[0]
    local_ser = tracer_local.events[0]
    assert remote_ser.checks == local_ser.checks
    assert remote_ser.io_delta == local_ser.io_delta
    assert remote_ser.action == local_ser.action
    assert len(stub.published) == len(fake_pipeline.resolved_spec)
