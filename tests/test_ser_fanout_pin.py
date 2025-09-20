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

from semantiva import Pipeline, Payload
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import (
    FloatMockDataSink,
    FloatMultiplyOperation,
    FloatValueDataSourceWithDefault,
)
from semantiva.trace.model import SERRecord, TraceDriver


class _CaptureTrace(TraceDriver):
    def __init__(self) -> None:
        self.events: list[SERRecord] = []

    def on_pipeline_start(
        self, pipeline_id, run_id, canonical_spec, meta, pipeline_input=None
    ):
        return None

    def on_node_event(self, event: SERRecord) -> None:
        self.events.append(event)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        return None

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_ser_records_include_fanout_arguments(tmp_path):
    trace = _CaptureTrace()
    pipeline = Pipeline(
        [
            {"processor": FloatValueDataSourceWithDefault},
            {"processor": FloatMultiplyOperation},
            {
                "processor": FloatMockDataSink,
                "parameters": {"path": str(tmp_path / "out.txt")},
            },
        ],
        trace=trace,
    )

    FANOUT_RUNS = [
        (
            {"value": 3.0, "factor": 2.0},
            {"fanout.index": 0, "fanout.mode": "multi_zip"},
        ),
        (
            {"value": 5.0, "factor": 4.0},
            {"fanout.index": 1, "fanout.mode": "multi_zip"},
        ),
    ]

    EXPECTED_VALUES = {
        0: {"value": 3.0, "factor": 2.0},
        1: {"value": 5.0, "factor": 4.0},
    }

    for values, base_args in FANOUT_RUNS:
        fanout_args = dict(base_args)
        fanout_args["fanout.values"] = values
        pipeline.set_run_metadata({"args": fanout_args})
        payload = Payload(NoDataType(), ContextType(values))
        pipeline.process(payload)

    assert trace.events, "expected SER events to be captured"
    run_ids = {event.ids["run_id"] for event in trace.events}
    assert len(run_ids) == len(FANOUT_RUNS)
    for event in trace.events:
        args = event.checks["why_ok"].get("args", {})
        assert "fanout.index" in args
        assert "fanout.mode" in args
        assert "fanout.values" in args
        index = args["fanout.index"]
        assert args["fanout.values"] == EXPECTED_VALUES[index]
