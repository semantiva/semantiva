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
from pathlib import Path
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline
from semantiva.trace.drivers.jsonl import JSONLTrace


def test_checks_fields_present(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path), detail="hash")
    Pipeline(nodes, trace=tracer).process()
    tracer.close()

    ser = next(
        json.loads(line)
        for line in trace_path.read_text().splitlines()
        if line.strip() and json.loads(line).get("type") == "ser"
    )
    checks = ser["checks"]
    assert checks["why_run"]["trigger"] == "dependency"
    assert isinstance(checks["why_run"]["upstream_evidence"], list)
    assert isinstance(checks["why_ok"]["post"], list)
    assert isinstance(checks["why_ok"]["env"], dict)
