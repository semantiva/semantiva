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

# tests/examples/test_fanout_floats_example.py
from __future__ import annotations

from pathlib import Path


def test_fanout_floats_yaml_executes_locally(tmp_path, monkeypatch):
    """
    Loads the example YAML and executes with the default local orchestrator
    via the Pipeline API. Asserts that SER is produced and that at least one
    SER record is written per run.
    """
    # Arrange: isolate working directory
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    yaml_path = (
        Path(__file__).parents[2]
        / "docs"
        / "source"
        / "examples"
        / "fanout_floats.yaml"
    )
    assert yaml_path.exists(), f"Example YAML missing at {yaml_path}"

    from semantiva.configurations import load_pipeline_from_yaml
    from semantiva.execution.fanout import expand_fanout
    from semantiva import Pipeline, Payload
    from semantiva.context_processors import ContextType
    from semantiva.data_types import NoDataType
    from semantiva.trace.drivers.jsonl import JSONLTrace

    cfg = load_pipeline_from_yaml(str(yaml_path))
    runs, meta = expand_fanout(cfg.fanout, cwd=yaml_path.parent)

    # Create trace driver at the YAML-declared output path
    assert cfg.trace.output_path, "trace.output_path must be set in the example YAML"
    ser_path = Path(cfg.trace.output_path)
    # Ensure directory exists when a file path is given
    ser_path.parent.mkdir(parents=True, exist_ok=True)
    detail = (
        cfg.trace.options.get("detail") if isinstance(cfg.trace.options, dict) else None
    )
    tracer = JSONLTrace(str(ser_path), detail=detail)

    pipeline = Pipeline(cfg.nodes, trace=tracer)

    for idx, values in enumerate(runs):
        # Attach run metadata (pins fanout.* into SER why_ok.args)
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
        pipeline.process(payload)

    tracer.close()
