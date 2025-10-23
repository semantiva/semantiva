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

from __future__ import annotations

from semantiva import Pipeline
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import (
    FloatMockDataSink,
    FloatMultiplyOperation,
    FloatValueDataSourceWithDefault,
)
from semantiva.pipeline import Payload
from semantiva.trace.model import SERRecord, TraceDriver
from semantiva.trace.runtime import TraceContext


class _CaptureRunSpaceTrace(TraceDriver):
    def __init__(self) -> None:
        self.pipeline_starts: list[dict[str, object]] = []

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        pipeline_spec_canonical: dict,
        meta: dict,
        pipeline_input: Payload | None = None,
        **kwargs: object,
    ) -> None:
        record = {
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "meta": meta,
            **kwargs,
        }
        self.pipeline_starts.append(record)

    def on_node_event(self, event: SERRecord) -> None:  # pragma: no cover - unused
        return None

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:  # pragma: no cover
        return None

    def flush(self) -> None:  # pragma: no cover
        return None

    def close(self) -> None:  # pragma: no cover
        return None


def test_pipeline_start_carries_run_space_fks(tmp_path):
    """Test that pipeline_start carries composite FK (launch_id + attempt), not spec_id/inputs_id."""
    driver = _CaptureRunSpaceTrace()
    pipeline = Pipeline(
        [
            {"processor": FloatValueDataSourceWithDefault},
            {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
            {
                "processor": FloatMockDataSink,
                "parameters": {"path": str(tmp_path / "out.txt")},
            },
        ],
        trace=driver,
    )

    trace_ctx = TraceContext()
    trace_ctx.set_run_space_fk(
        spec_id="a" * 64,
        launch_id="launch-id",
        attempt=3,
        inputs_id="b" * 64,
    )
    pipeline.set_run_metadata(
        {
            "trace_context": trace_ctx,
            "run_space_index": 0,
            "run_space_context": {"value": 1.0},
        }
    )

    pipeline.process(Payload(NoDataType(), ContextType({})))

    assert driver.pipeline_starts, "expected pipeline_start to be emitted"
    record = driver.pipeline_starts[0]
    # Verify composite FK (launch_id + attempt), not spec_id/inputs_id
    assert record["run_space_launch_id"] == "launch-id"
    assert record["run_space_attempt"] == 3
    assert record["run_space_index"] == 0
    assert record["run_space_context"] == {"value": 1.0}
    # Verify spec_id and inputs_id are NOT in pipeline_start
    assert "run_space_spec_id" not in record
    assert "run_space_inputs_id" not in record
