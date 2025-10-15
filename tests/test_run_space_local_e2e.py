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

from pathlib import Path

from semantiva import Pipeline, Payload
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.execution.run_space import expand_run_space
from semantiva.trace.drivers.jsonl import JsonlTraceDriver


def test_local_run_space_runs_end_to_end(tmp_path, monkeypatch):
    cfg_path = Path("examples/pipelines/run_space_demo.yaml").resolve()
    pipeline_cfg = load_pipeline_from_yaml(str(cfg_path))

    runs, meta = expand_run_space(pipeline_cfg.run_space, cwd=cfg_path.parent)
    assert runs, "Expected run-space expansions"

    monkeypatch.chdir(tmp_path)
    (tmp_path / "outputs").mkdir(exist_ok=True)

    trace_dir = tmp_path / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_driver = JsonlTraceDriver(str(trace_dir))
    pipeline = Pipeline(
        pipeline_cfg.nodes,
        trace=trace_driver,
    )

    outputs = []
    total = len(runs)
    for idx, values in enumerate(runs):
        run_args = {
            "run_space.index": idx,
            "run_space.total": total,
            "run_space.combine": meta.get("combine", "product"),
            "run_space.context": dict(values),
        }
        pipeline.set_run_metadata({"args": run_args, "run_space": meta})
        payload = Payload(NoDataType(), ContextType(dict(values)))
        result = pipeline.process(payload)
        outputs.append(result.data.data)

    trace_driver.close()

    expected = [(vals["value"] + vals["addend"]) * vals["factor"] for vals in runs]
    assert outputs == expected
    ser_files = list(trace_dir.glob("*.ser.jsonl"))
    assert ser_files, "SER file not created for run-space run"
