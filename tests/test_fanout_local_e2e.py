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
from semantiva.execution.fanout import expand_fanout
from semantiva.trace.drivers.jsonl import JSONLTrace


def test_local_fanout_runs_end_to_end(tmp_path):
    cfg_path = Path("docs/source/examples/fanout_basic_local.yaml").resolve()
    pipeline_cfg = load_pipeline_from_yaml(str(cfg_path))

    runs, meta = expand_fanout(pipeline_cfg.fanout, cwd=cfg_path.parent)
    assert runs, "Expected fan-out runs"

    trace_dir = tmp_path / "trace"
    trace_driver = JSONLTrace(str(trace_dir))
    pipeline = Pipeline(
        pipeline_cfg.nodes,
        trace=trace_driver,
    )

    outputs = []
    for idx, values in enumerate(runs):
        fanout_args = {
            "fanout.index": idx,
            "fanout.mode": meta.get("mode", "single"),
            "fanout.values": values,
        }
        if "source_file" in meta:
            fanout_args["fanout.source_file"] = meta["source_file"]
        if "source_sha256" in meta:
            fanout_args["fanout.source_sha256"] = meta["source_sha256"]
        pipeline.set_run_metadata({"args": fanout_args})
        payload = Payload(NoDataType(), ContextType(values))
        result = pipeline.process(payload)
        outputs.append(result.data.data)

    trace_driver.close()

    expected = [vals["value"] * vals["factor"] for vals in runs]
    assert outputs == expected
    ser_files = list(trace_dir.glob("*.ser.jsonl"))
    assert ser_files, "SER file not created for fan-out run"
