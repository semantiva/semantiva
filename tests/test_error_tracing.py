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
Tests for error tracing functionality.

Verifies that the trace system properly captures and records execution errors,
including before/error events, timing data, and proper trace file closure.
"""

import json
import tempfile
import pytest
from pathlib import Path
from typing import List, Optional

from semantiva.trace.drivers.jsonl import JSONLTrace
from semantiva.trace.model import NodeTraceEvent
from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.data_processors.data_processors import DataOperation
from semantiva.examples.test_utils import FloatDataType
from semantiva import Payload
from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.logger import Logger


class FailingFloatOperation(DataOperation):
    """A test operation that always fails with a specific error."""

    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType

    def _process_logic(
        self, data: FloatDataType, error_message: str = "Test failure"
    ) -> FloatDataType:
        raise ValueError(error_message)


class MockTraceCapture:
    """Test driver that captures all trace events in memory."""

    def __init__(self) -> None:
        self.events: List[dict] = []
        self.pipeline_start_event: Optional[dict] = None
        self.pipeline_end_event: Optional[dict] = None

    def on_pipeline_start(
        self, pipeline_id: str, run_id: str, canonical_spec: dict, meta: dict, **kwargs
    ) -> None:
        self.pipeline_start_event = {
            "type": "pipeline_start",
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "canonical_spec": canonical_spec,
            "meta": meta,
        }

    def on_node_event(self, event: NodeTraceEvent) -> None:
        self.events.append(
            {
                "type": "node",
                "phase": event.phase,
                "address": event.address,
                "error_type": event.error_type,
                "error_msg": event.error_msg,
                "t_wall": event.t_wall,
                "t_cpu": event.t_cpu,
                "event_time_utc": event.event_time_utc,
            }
        )

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        self.pipeline_end_event = {
            "type": "pipeline_end",
            "run_id": run_id,
            "summary": summary,
        }

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


def test_error_tracing_captures_events():
    """Test that error tracing captures before and error events with timing."""
    # Setup
    trace = MockTraceCapture()
    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()

    # Pipeline specification referencing the failing operation
    pipeline_spec = [
        {
            "processor": FailingFloatOperation,
            "parameters": {"error_message": "Test error message"},
        }
    ]

    # Execute and expect failure
    initial_payload = Payload(FloatDataType(5.0), {})

    with pytest.raises(ValueError, match="Test error message"):
        orchestrator.execute(
            pipeline_spec=pipeline_spec,
            payload=initial_payload,
            transport=transport,
            logger=logger,
            trace=trace,
        )

    # Verify trace events were captured
    assert trace.pipeline_start_event is not None
    assert trace.pipeline_end_event is not None
    assert len(trace.events) == 2  # before + error

    # Verify before event
    before_event = trace.events[0]
    assert before_event["phase"] == "before"
    assert before_event["error_type"] is None
    assert before_event["error_msg"] is None
    assert before_event["t_wall"] is None
    assert before_event["t_cpu"] is None

    # Verify error event
    error_event = trace.events[1]
    assert error_event["phase"] == "error"
    assert error_event["error_type"] == "ValueError"
    assert error_event["error_msg"] == "Test error message"
    assert error_event["t_wall"] is not None
    assert error_event["t_cpu"] is not None
    assert error_event["t_wall"] >= 0
    assert error_event["t_cpu"] >= 0

    # Verify pipeline end shows error status
    assert trace.pipeline_end_event["summary"]["status"] == "error"
    assert "Test error message" in trace.pipeline_end_event["summary"]["error"]


def test_jsonl_error_tracing_writes_to_file():
    """Test that JSONL trace driver properly writes error events to file."""
    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        trace_file = Path(temp_dir) / "test_error_trace"
        trace = JSONLTrace(trace_file, detail="all")

        orchestrator = LocalSemantivaOrchestrator()
        transport = InMemorySemantivaTransport()
        logger = Logger()

        pipeline_spec = [
            {
                "processor": FailingFloatOperation,
                "parameters": {"error_message": "JSONL test error"},
            }
        ]

        # Execute and expect failure
        initial_payload = Payload(FloatDataType(10.0), {})

        with pytest.raises(ValueError, match="JSONL test error"):
            orchestrator.execute(
                pipeline_spec=pipeline_spec,
                payload=initial_payload,
                transport=transport,
                logger=logger,
                trace=trace,
            )

        # Give the background thread a moment to write files
        time.sleep(0.1)

        # Find the generated JSONL file (it might be in a subdirectory)
        jsonl_files = list(Path(temp_dir).rglob("*.jsonl"))
        assert len(jsonl_files) == 1

        # Parse and verify JSONL content
        with open(jsonl_files[0], "r") as f:
            content = f.read().strip()

        # Split by double newlines (JSONL format separates records)
        records = [json.loads(line) for line in content.split("\n\n") if line.strip()]

        # Should have: pipeline_start, node(before), node(error), pipeline_end
        assert len(records) == 4

        # Verify record types and order
        assert records[0]["type"] == "pipeline_start"
        assert records[1]["type"] == "node" and records[1]["phase"] == "before"
        assert records[2]["type"] == "node" and records[2]["phase"] == "error"
        assert records[3]["type"] == "pipeline_end"

        # Verify error details in error record
        error_record = records[2]
        assert error_record["error_type"] == "ValueError"
        assert error_record["error_msg"] == "JSONL test error"
        assert "t_wall" in error_record
        assert "t_cpu" in error_record

        # Verify pipeline_end shows error
        pipeline_end = records[3]
        assert pipeline_end["summary"]["status"] == "error"
        assert "JSONL test error" in pipeline_end["summary"]["error"]


def test_multiple_nodes_error_in_middle():
    """Test error tracing when error occurs in the middle of a multi-node pipeline."""
    trace = MockTraceCapture()
    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()

    # Create pipeline: working -> failing -> working
    from semantiva.examples.test_utils import FloatMultiplyOperation

    pipeline_spec = [
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
        {
            "processor": FailingFloatOperation,
            "parameters": {"error_message": "Middle node failure"},
        },
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 3.0}},
    ]

    initial_payload = Payload(FloatDataType(5.0), {})

    with pytest.raises(ValueError, match="Middle node failure"):
        orchestrator.execute(
            pipeline_spec=pipeline_spec,
            payload=initial_payload,
            transport=transport,
            logger=logger,
            trace=trace,
        )

    # Should have: node1(before+after), node2(before+error), no node3 events
    assert len(trace.events) == 4

    # Node 1: before + after (successful)
    assert trace.events[0]["phase"] == "before"
    assert trace.events[1]["phase"] == "after"
    assert trace.events[1]["error_type"] is None

    # Node 2: before + error (failed)
    assert trace.events[2]["phase"] == "before"
    assert trace.events[3]["phase"] == "error"
    assert trace.events[3]["error_type"] == "ValueError"
    assert trace.events[3]["error_msg"] == "Middle node failure"

    # Pipeline should show error status
    assert trace.pipeline_end_event["summary"]["status"] == "error"


def test_error_tracing_with_different_exception_types():
    """Test that different exception types are properly captured."""
    test_cases = [
        (TypeError("Type error message"), "TypeError", "Type error message"),
        (
            RuntimeError("Runtime error message"),
            "RuntimeError",
            "Runtime error message",
        ),
        (KeyError("missing_key"), "KeyError", "'missing_key'"),
        (
            AttributeError("'NoneType' object has no attribute 'foo'"),
            "AttributeError",
            "'NoneType' object has no attribute 'foo'",
        ),
    ]

    for exc, expected_type, expected_msg in test_cases:
        trace = MockTraceCapture()
        orchestrator = LocalSemantivaOrchestrator()
        transport = InMemorySemantivaTransport()
        logger = Logger()

        # Create failing operation that raises specific exception
        class CustomFailingOperation(DataOperation):
            @classmethod
            def input_data_type(cls):
                return FloatDataType

            @classmethod
            def output_data_type(cls):
                return FloatDataType

            def _process_logic(self, data: FloatDataType) -> FloatDataType:
                raise exc

        pipeline_spec = [{"processor": CustomFailingOperation, "parameters": {}}]
        initial_payload = Payload(FloatDataType(1.0), {})

        with pytest.raises(type(exc)):
            orchestrator.execute(
                pipeline_spec=pipeline_spec,
                payload=initial_payload,
                transport=transport,
                logger=logger,
                trace=trace,
            )

        # Verify error event captures correct exception details
        error_event = trace.events[1]  # [before, error]
        assert error_event["phase"] == "error"
        assert error_event["error_type"] == expected_type
        assert error_event["error_msg"] == expected_msg
