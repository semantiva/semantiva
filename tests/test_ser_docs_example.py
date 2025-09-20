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


def _extract_example(path: Path) -> dict:
    text = path.read_text().splitlines()
    start_idx = None
    for idx, line in enumerate(text):
        if line.strip().startswith(".. code-block:: json"):
            start_idx = idx
            break
    if start_idx is None:
        raise ValueError("Example code block not found")
    block: list[str] = []
    for line in text[start_idx + 1 :]:
        if line.strip() == "" and not block:
            continue
        if line.startswith("   "):
            block.append(line[3:])
            continue
        if block:
            break
    return json.loads("\n".join(block))


def test_docs_ser_example_parity(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path), detail="hash")
    Pipeline(nodes, trace=tracer).process()
    tracer.close()
    real_ser = next(
        json.loads(line)
        for line in trace_path.read_text().splitlines()
        if line and json.loads(line).get("type") == "ser"
    )
    example = _extract_example(Path("docs/source/ser.rst"))
    assert set(example.keys()) == set(real_ser.keys())
