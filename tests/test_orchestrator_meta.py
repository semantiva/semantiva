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

"""Test orchestrator emission of semantic_id and config_id in meta dict."""

import pytest

from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.examples.test_utils import (
    FloatDataType,
    FloatMultiplyOperation,
    FloatDivideOperation,
)
from semantiva.pipeline.payload import Payload
from semantiva.context_processors import ContextType
from semantiva.execution.transport import InMemorySemantivaTransport
from semantiva.logger import Logger


class MetaCaptureTrace:
    """Trace driver that captures the meta dict from pipeline_start."""

    def __init__(self):
        self.captured_meta = None
        self.pipeline_id = None
        self.run_id = None

    def on_pipeline_start(self, pipeline_id, run_id, canonical, meta, **kwargs):
        self.pipeline_id = pipeline_id
        self.run_id = run_id
        self.captured_meta = meta

    def on_node_event(self, *args, **kwargs):
        pass

    def on_pipeline_end(self, *args, **kwargs):
        pass

    def flush(self):
        pass

    def close(self):
        pass


def test_orchestrator_emits_semantic_id_in_meta():
    """Verify orchestrator includes semantic_id in meta dict."""
    spec = [{"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType())

    trace = MetaCaptureTrace()
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )

    assert trace.captured_meta is not None
    assert "semantic_id" in trace.captured_meta
    assert trace.captured_meta["semantic_id"].startswith("plsemid-")


def test_orchestrator_emits_config_id_in_meta():
    """Verify orchestrator includes config_id in meta dict."""
    spec = [{"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType())

    trace = MetaCaptureTrace()
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )

    assert trace.captured_meta is not None
    assert "config_id" in trace.captured_meta
    assert trace.captured_meta["config_id"].startswith("plcid-")


def test_orchestrator_semantic_id_and_config_id_are_distinct():
    """Verify that semantic_id and config_id are different values."""
    spec = [{"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType())

    trace = MetaCaptureTrace()
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )

    assert trace.captured_meta["semantic_id"] != trace.captured_meta["config_id"]


def test_orchestrator_semantic_id_deterministic():
    """Verify that same pipeline structure produces same semantic_id."""
    spec = [
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
        {"processor": FloatDivideOperation, "parameters": {"divisor": 2.0}},
    ]
    payload = Payload(FloatDataType(1.0), ContextType())

    # First run
    trace1 = MetaCaptureTrace()
    orch1 = LocalSemantivaOrchestrator()
    orch1.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace1,
    )

    # Second run with same spec
    trace2 = MetaCaptureTrace()
    orch2 = LocalSemantivaOrchestrator()
    orch2.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace2,
    )

    # Same pipeline structure should have same semantic_id
    assert trace1.captured_meta["semantic_id"] == trace2.captured_meta["semantic_id"]


def test_orchestrator_includes_node_semantic_ids():
    """Verify that node_semantic_ids are included in meta."""
    spec = [{"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType())

    trace = MetaCaptureTrace()
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )

    assert "node_semantic_ids" in trace.captured_meta
    assert isinstance(trace.captured_meta["node_semantic_ids"], dict)


def test_orchestrator_meta_includes_num_nodes():
    """Verify that num_nodes field is present in meta."""
    spec = [
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
        {"processor": FloatDivideOperation, "parameters": {"divisor": 2.0}},
    ]
    payload = Payload(FloatDataType(1.0), ContextType())

    trace = MetaCaptureTrace()
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )

    assert "num_nodes" in trace.captured_meta
    assert trace.captured_meta["num_nodes"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
