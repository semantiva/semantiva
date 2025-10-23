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

import json

from semantiva import Pipeline
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import (
    FloatMockDataSink,
    FloatMultiplyOperation,
    FloatValueDataSourceWithDefault,
)
from semantiva.pipeline import Payload
from semantiva.trace.drivers.jsonl import JsonlTraceDriver
from semantiva.trace.runtime import (
    RunSpaceIdentityService,
    RunSpaceLaunchManager,
    RunSpaceTraceEmitter,
    TraceContext,
)


def _build_pipeline(tmp_path, trace_driver):
    return Pipeline(
        [
            {"processor": FloatValueDataSourceWithDefault},
            {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
            {
                "processor": FloatMockDataSink,
                "parameters": {"path": str(tmp_path / "out.txt")},
            },
        ],
        trace=trace_driver,
    )


def _load_records(path):
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def test_full_flow_self_contained(tmp_path):
    driver = JsonlTraceDriver(output_path=tmp_path)
    emitter = RunSpaceTraceEmitter(driver)
    launch = RunSpaceLaunchManager().create_launch(
        run_space_spec_id="a" * 64,
        run_space_inputs_id=None,
    )
    trace_ctx = TraceContext()
    trace_ctx.set_run_space_fk(
        spec_id="a" * 64,
        launch_id=launch.id,
        attempt=launch.attempt,
    )

    emitter.emit_start(
        run_space_spec_id="a" * 64,
        run_space_launch_id=launch.id,
        run_space_attempt=launch.attempt,
        run_space_combine_mode="combinatorial",
        run_space_total_runs=1,
        run_space_planned_run_count=1,
    )

    pipeline = _build_pipeline(tmp_path, driver)
    pipeline.set_run_metadata(
        {
            "trace_context": trace_ctx,
            "run_space_index": 0,
            "run_space_context": {},
        }
    )
    pipeline.process(Payload(NoDataType(), ContextType({})))

    emitter.emit_end(
        run_space_launch_id=launch.id,
        run_space_attempt=launch.attempt,
        summary={"completed_runs": 1},
    )
    driver.close()

    # In directory mode, run_space lifecycle events are in separate .trace.jsonl file
    trace_files = list(tmp_path.glob("*.trace.jsonl"))
    ser_files = list(tmp_path.glob("*.ser.jsonl"))
    assert ser_files, "expected JSONL trace to be written"

    # Load run_space lifecycle events from dedicated file
    assert trace_files, "expected run_space trace file to be written"
    runspace_records = _load_records(trace_files[0])
    assert any(rec["record_type"] == "run_space_start" for rec in runspace_records)
    assert any(rec["record_type"] == "run_space_end" for rec in runspace_records)

    # Load pipeline events from main trace file
    records = _load_records(ser_files[0])
    pipeline_start = next(
        rec for rec in records if rec["record_type"] == "pipeline_start"
    )
    # Verify composite FK (launch_id + attempt), not spec_id/inputs_id
    assert pipeline_start["run_space_launch_id"] == launch.id
    assert pipeline_start["run_space_attempt"] == launch.attempt
    assert pipeline_start["run_space_index"] == 0
    assert pipeline_start["run_space_context"] == {}
    assert "run_space_spec_id" not in pipeline_start
    assert "run_space_inputs_id" not in pipeline_start


def test_full_flow_with_file_inputs(tmp_path):
    data_file = tmp_path / "values.csv"
    data_file.write_text("value\n1\n", encoding="utf-8")

    spec = {
        "combine": "product",
        "max_runs": 10,
        "dry_run": False,
        "blocks": [
            {
                "mode": "zip",
                "context": {"value": [1]},
                "source": {
                    "format": "csv",
                    "path": str(data_file),
                    "select": None,
                    "rename": {},
                    "mode": "zip",
                },
            }
        ],
    }
    identity = RunSpaceIdentityService().compute(spec, base_dir=tmp_path)
    launch = RunSpaceLaunchManager().create_launch(
        run_space_spec_id=identity.spec_id,
        run_space_inputs_id=identity.inputs_id,
    )

    driver = JsonlTraceDriver(output_path=tmp_path)
    emitter = RunSpaceTraceEmitter(driver)
    trace_ctx = TraceContext()
    trace_ctx.set_run_space_fk(
        spec_id=identity.spec_id,
        launch_id=launch.id,
        attempt=launch.attempt,
        inputs_id=identity.inputs_id,
    )

    emitter.emit_start(
        run_space_spec_id=identity.spec_id,
        run_space_launch_id=launch.id,
        run_space_attempt=launch.attempt,
        run_space_combine_mode="product",
        run_space_total_runs=1,
        run_space_inputs_id=identity.inputs_id,
        run_space_input_fingerprints=identity.fingerprints,
        run_space_planned_run_count=1,
    )

    pipeline = _build_pipeline(tmp_path, driver)
    pipeline.set_run_metadata(
        {
            "trace_context": trace_ctx,
            "run_space_index": 0,
            "run_space_context": {"value": 1},
        }
    )
    pipeline.process(Payload(NoDataType(), ContextType({})))

    emitter.emit_end(
        run_space_launch_id=launch.id,
        run_space_attempt=launch.attempt,
        summary={"completed_runs": 1},
    )
    driver.close()

    # In directory mode, run_space lifecycle events are in separate .trace.jsonl file
    trace_files = list(tmp_path.glob("*.trace.jsonl"))
    ser_files = list(tmp_path.glob("*.ser.jsonl"))
    assert ser_files, "expected JSONL trace to be written"

    # Load run_space lifecycle events from dedicated file
    assert trace_files, "expected run_space trace file to be written"
    runspace_records = _load_records(trace_files[0])
    run_space_start = next(
        rec for rec in runspace_records if rec["record_type"] == "run_space_start"
    )
    assert run_space_start["run_space_inputs_id"] == identity.inputs_id
    assert run_space_start["run_space_input_fingerprints"]
    assert run_space_start["run_space_combine_mode"] == "product"
    assert run_space_start["run_space_total_runs"] == 1

    # Load pipeline events from main trace file
    records = _load_records(ser_files[-1])
    pipeline_start = next(
        rec for rec in records if rec["record_type"] == "pipeline_start"
    )
    # Verify composite FK (launch_id + attempt), not spec_id/inputs_id
    assert pipeline_start["run_space_launch_id"] == launch.id
    assert pipeline_start["run_space_attempt"] == launch.attempt
    assert pipeline_start["run_space_index"] == 0
    assert pipeline_start["run_space_context"] == {"value": 1}
    assert "run_space_inputs_id" not in pipeline_start
    assert "run_space_spec_id" not in pipeline_start
