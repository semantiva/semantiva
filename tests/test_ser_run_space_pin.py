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
        self, pipeline_id, run_id, pipeline_spec_canonical, meta, pipeline_input=None
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


def test_ser_records_include_run_space_arguments(tmp_path):
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

    RUNS = [
        (
            {"value": 3.0, "factor": 2.0},
            {
                "run_space.index": 0,
                "run_space.total": 2,
                "run_space.combine": "product",
            },
        ),
        (
            {"value": 5.0, "factor": 4.0},
            {
                "run_space.index": 1,
                "run_space.total": 2,
                "run_space.combine": "product",
            },
        ),
    ]

    run_space_meta = {
        "combine": "product",
        "max_runs": 10,
        "expanded_runs": 2,
        "blocks": [
            {
                "mode": "zip",
                "size": 2,
                "context_keys": ["value", "factor"],
            }
        ],
    }

    for values, base_args in RUNS:
        run_args = dict(base_args)
        run_args["run_space.context"] = values
        pipeline.set_run_metadata({"args": run_args, "run_space": run_space_meta})
        payload = Payload(NoDataType(), ContextType(values))
        pipeline.process(payload)

    assert trace.events, "expected SER events to be captured"
    run_ids = {event.identity["run_id"] for event in trace.events}
    assert len(run_ids) == len(RUNS)
    for event in trace.events:
        args = event.assertions.get("args", {})
        assert "run_space.index" in args
        assert "run_space.combine" in args
        assert "run_space.context" in args
        index = args["run_space.index"]
        assert args["run_space.context"] == RUNS[index][0]
