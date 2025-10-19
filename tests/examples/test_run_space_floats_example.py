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

from pathlib import Path


def test_run_space_floats_yaml_executes_locally(tmp_path, monkeypatch):
    """Execute the run_space example and assert SER is produced."""

    cwd = tmp_path
    monkeypatch.chdir(cwd)

    yaml_path = (
        Path(__file__).parents[2]
        / "docs"
        / "source"
        / "examples"
        / "run_space_floats.yaml"
    )
    assert yaml_path.exists(), f"Example YAML missing at {yaml_path}"

    from semantiva.configurations import load_pipeline_from_yaml
    from semantiva.execution.run_space import expand_run_space
    from semantiva import Pipeline, Payload
    from semantiva.context_processors import ContextType
    from semantiva.data_types import NoDataType
    from semantiva.trace.drivers.jsonl import JsonlTraceDriver

    cfg = load_pipeline_from_yaml(str(yaml_path))
    runs, meta = expand_run_space(cfg.run_space, cwd=yaml_path.parent)

    assert cfg.trace.output_path, "trace.output_path must be set in the example YAML"
    ser_path = Path(cfg.trace.output_path)
    ser_path.parent.mkdir(parents=True, exist_ok=True)
    detail = (
        cfg.trace.options.get("detail") if isinstance(cfg.trace.options, dict) else None
    )
    tracer = JsonlTraceDriver(str(ser_path), detail=detail)

    pipeline = Pipeline(cfg.nodes, trace=tracer)

    total = len(runs)
    for idx, values in enumerate(runs):
        run_args = {
            "run_space.index": idx,
            "run_space.total": total,
            "run_space.combine": meta.get("combine", "combinatorial"),
            "run_space.context": dict(values),
        }
        pipeline.set_run_metadata({"args": run_args, "run_space": meta})
        payload = Payload(NoDataType(), ContextType(dict(values)))
        pipeline.process(payload)

    tracer.close()

    assert ser_path.exists()
