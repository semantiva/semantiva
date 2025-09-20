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
from importlib import resources

import pytest

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency
    jsonschema = None
    pytest.skip("jsonschema not installed", allow_module_level=True)

from semantiva import Payload
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.data_processors.data_processors import DataOperation
from semantiva.examples.test_utils import FloatDataType
from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.logger import Logger
from semantiva.pipeline import Pipeline
from semantiva.pipeline.payload import ContextType
from semantiva.trace.drivers.jsonl import JSONLTrace


def test_ser_schema_validation(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))
    Pipeline(nodes, trace=tracer).process()
    tracer.close()
    schema_path = resources.files("semantiva.trace.schema") / "ser_v0.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for line in trace_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("type") == "ser":
            validator.validate(rec)


class _FailingOperation(DataOperation):
    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType

    def _process_logic(self, data: FloatDataType) -> FloatDataType:
        raise RuntimeError("boom")


def test_ser_schema_validation_error_path(tmp_path: Path) -> None:
    schema_path = resources.files("semantiva.trace.schema") / "ser_v0.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()
    trace_path = tmp_path / "error.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))

    payload = Payload(FloatDataType(1.0), ContextType({}))
    pipeline_spec = [{"processor": _FailingOperation, "parameters": {}}]

    with pytest.raises(RuntimeError):
        orchestrator.execute(
            pipeline_spec=pipeline_spec,
            payload=payload,
            transport=transport,
            logger=logger,
            trace=tracer,
        )

    tracer.close()
    for line in trace_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("type") == "ser":
            validator.validate(rec)
