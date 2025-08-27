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

import json
from pathlib import Path
import subprocess
import sys


def run_cli(args, cwd: Path | None = None):
    cmd = [sys.executable, "-m", "semantiva.semantiva", *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def test_cli_pipeline_model_fitting_jsonl(tmp_path: Path):
    output_dir = tmp_path / "trace"
    output_dir.mkdir()
    res = run_cli(
        [
            "run",
            "tests/pipeline_model_fitting.yaml",
            "--trace-driver",
            "jsonl",
            "--trace-detail",
            "all",
            "--trace-output",
            str(output_dir),
            "--context",
            "x_values=[0,1,2]",
            "--context",
            "y_values=[1,3,7]",
        ]
    )
    assert res.returncode == 0
    files = list(output_dir.glob("*.jsonl"))
    assert files, "trace file not created"
    content = [c for c in files[0].read_text().split("\n\n") if c.strip()]
    records = [json.loads(chunk) for chunk in content]
    start = next(r for r in records if r["type"] == "pipeline_start")
    json.dumps(start["canonical_spec"])


def test_cli_pipeline_with_duplicate_nodes(tmp_path: Path):
    yaml_content = """
pipeline:
  nodes:
    - processor: FloatValueDataSource
    - processor: FloatMultiplyOperation
      parameters:
        factor: 2.0
    - processor: FloatMultiplyOperation
      parameters:
        factor: 3.0
"""
    yaml_path = tmp_path / "dup.yaml"
    yaml_path.write_text(yaml_content)
    output_dir = tmp_path / "trace"
    output_dir.mkdir()
    res = run_cli(
        [
            "run",
            str(yaml_path),
            "--trace-driver",
            "jsonl",
            "--trace-output",
            str(output_dir),
        ]
    )
    assert res.returncode == 0
    files = list(output_dir.glob("*.jsonl"))
    assert files
    content = [c for c in files[0].read_text().split("\n\n") if c.strip()]
    records = [json.loads(chunk) for chunk in content]
    start = next(r for r in records if r["type"] == "pipeline_start")
    node_uuids = [n["node_uuid"] for n in start["canonical_spec"]["nodes"]]
    assert len(node_uuids) == len(set(node_uuids))
