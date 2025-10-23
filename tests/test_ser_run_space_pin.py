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
        self,
        pipeline_id,
        run_id,
        pipeline_spec_canonical,
        meta,
        pipeline_input=None,
        **_: object,
    ):
        return None

    def on_node_event(self, event: SERRecord) -> None:
        self.events.append(event)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        return None

    def on_run_space_start(
        self,
        run_id: str,
        *,
        run_space_spec_id: str,
        run_space_launch_id: str,
        run_space_attempt: int,
        run_space_combine_mode: str,
        run_space_total_runs: int,
        run_space_max_runs_limit: int | None = None,
        run_space_inputs_id: str | None = None,
        run_space_input_fingerprints: list[dict] | None = None,
        run_space_planned_run_count: int | None = None,
    ) -> None:
        return None

    def on_run_space_end(
        self,
        run_id: str,
        *,
        run_space_launch_id: str,
        run_space_attempt: int,
        summary: dict | None = None,
    ) -> None:
        return None

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_ser_records_include_run_space_arguments(tmp_path):
    """Test that run_space data is NO LONGER in SER args (moved to pipeline_start)."""
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
        {"value": 3.0, "factor": 2.0},
        {"value": 5.0, "factor": 4.0},
    ]

    for idx, values in enumerate(RUNS):
        # New: pass index/context in metadata, not args
        pipeline.set_run_metadata(
            {
                "run_space_index": idx,
                "run_space_context": values,
            }
        )
        payload = Payload(NoDataType(), ContextType(values))
        pipeline.process(payload)

    assert trace.events, "expected SER events to be captured"
    run_ids = {event.identity["run_id"] for event in trace.events}
    assert len(run_ids) == len(RUNS)

    # Verify SER args are now EMPTY (no run_space pollution)
    for event in trace.events:
        args = event.assertions.get("args", {})
        assert "run_space.index" not in args
        assert "run_space.combine" not in args
        assert "run_space.context" not in args
        assert "run_space.total" not in args
        # Args should be empty
        assert args == {}
