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

"""Integration tests for the CLI run command using ECR-only configuration."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap


def test_cli_runs_with_ecr_aliases(tmp_path):
    pipeline_yaml = tmp_path / "pipeline.yaml"
    trace_path = tmp_path / "trace.jsonl"
    sink_path = tmp_path / "sink.txt"
    pipeline_yaml.write_text(
        textwrap.dedent(
            f"""
            extensions: ["semantiva-examples"]
            pipeline:
              nodes:
                - processor: FloatValueDataSource
                  parameters: {{ value: 2.0 }}
                - processor: FloatMultiplyOperation
                  parameters: {{ factor: 3.0 }}
                - processor: FloatMockDataSink
                  parameters: {{ path: "{sink_path}" }}
            execution:
              orchestrator: local
              executor: sequential
              transport: in_memory
            trace:
              driver: jsonl
              output_path: "{trace_path}"
            """
        ).strip()
    )

    result = subprocess.run(
        [sys.executable, "-m", "semantiva.cli", "run", str(pipeline_yaml)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert trace_path.exists()
    lines = trace_path.read_text().splitlines()
    assert lines, "trace file must not be empty"
    json.loads(lines[0])
