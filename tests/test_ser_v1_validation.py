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

"""Test that SER v1 schema is correctly emitted and validated."""

from __future__ import annotations

import json
from pathlib import Path

from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline
from semantiva.trace.drivers.jsonl import JsonlTraceDriver


def test_ser_v1_schema_version_emitted(tmp_path: Path) -> None:
    """Test that all emitted SER records use schema_version=1."""
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    Pipeline(nodes, trace=tracer).process()
    tracer.close()

    for line in trace_path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        # All records should have schema_version=1
        assert (
            record["schema_version"] == 1
        ), f"Record {record.get('record_type', 'unknown')} has schema_version {record['schema_version']}, expected 1"


def test_no_legacy_schema_versions(tmp_path: Path) -> None:
    """Test that no legacy schema versions (0, 2, etc.) are emitted."""
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    Pipeline(nodes, trace=tracer).process()
    tracer.close()

    legacy_versions = []
    for line in trace_path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        version = record["schema_version"]
        if version != 1:
            legacy_versions.append((record.get("record_type", "unknown"), version))

    assert (
        not legacy_versions
    ), f"Found records with legacy schema versions: {legacy_versions}"
