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

from semantiva.trace.drivers.jsonl import JSONLTrace
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline


def test_io_delta_created_and_updated(tmp_path: Path) -> None:
    # Uses tests/simple_pipeline.yaml which writes to context (via probe) and modifies keys downstream if present.
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path), detail="hash")  # hash summaries only
    Pipeline(nodes, trace=tracer).process()
    tracer.close()

    sers = []
    for line in trace_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("type") == "ser":
            sers.append(rec)

    assert sers, "No SER records found"
    assert all("io_delta" in r for r in sers)
    # At least one node should create/update something in context over the demo pipeline.
    assert any(r["io_delta"]["created"] or r["io_delta"]["updated"] for r in sers)
    # Summaries for changed keys should include sha256 with detail=hash
    any_summary_has_sha = any(
        any("sha256" in s for s in r["io_delta"]["summaries"].values()) for r in sers
    )
    assert any_summary_has_sha
