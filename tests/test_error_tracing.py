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

"""Tests for error handling in SER tracing."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from semantiva.trace.drivers.jsonl import JsonlTraceDriver
from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.data_processors.data_processors import DataOperation
from semantiva.examples.test_utils import FloatDataType
from semantiva import Payload
from semantiva.pipeline.payload import ContextType
from typing import cast
from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.logger import Logger


class FailingFloatOperation(DataOperation):
    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType

    def _process_logic(self, data: FloatDataType, msg: str = "boom") -> FloatDataType:
        raise ValueError(msg)


def test_error_tracing_writes_failure(tmp_path: Path) -> None:
    orchestrator = LocalSemantivaOrchestrator()
    transport = InMemorySemantivaTransport()
    logger = Logger()
    trace = JsonlTraceDriver(str(tmp_path))

    pipeline_spec = [
        {"processor": FailingFloatOperation, "parameters": {"msg": "fail"}}
    ]
    payload = Payload(FloatDataType(1.0), cast(ContextType, {}))

    with pytest.raises(ValueError):
        orchestrator.execute(
            pipeline_spec=pipeline_spec,
            payload=payload,
            transport=transport,
            logger=logger,
            trace=trace,
        )

    trace.close()
    file = next(tmp_path.glob("*.ser.jsonl"))
    records = [json.loads(line) for line in file.read_text().splitlines() if line]
    ser = next(r for r in records if r["record_type"] == "ser")
    assert ser["status"] == "error"
    assert ser["error"]["type"] == "ValueError"
    post_checks = ser["assertions"]["postconditions"]
    assert post_checks[0]["code"] == "ValueError"
    assert post_checks[0]["result"] == "FAIL"
    codes = {entry["code"] for entry in post_checks}
    assert {"output_type_ok", "context_writes_realized"}.issubset(codes)
    env = ser["assertions"]["environment"]
    assert {"python", "platform", "semantiva"}.issubset(env)
    assert ser["processor"]["parameters"]["msg"] == "fail"
    assert ser["processor"]["parameter_sources"]["msg"] == "node"
    pipeline_end = records[-1]
    assert pipeline_end["record_type"] == "pipeline_end"
    assert pipeline_end["summary"]["status"] == "error"
