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

from semantiva import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.trace.drivers.jsonl import JSONLTrace
from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.logger import Logger
from semantiva.examples.test_utils import FloatDataType
from semantiva.data_processors.data_processors import DataOperation


class ParamOp(DataOperation):
    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType

    @staticmethod
    def get_required_keys():
        return ["from_ctx"]

    @staticmethod
    def get_default_params():
        return {"defaulted": 3.0}

    def _process_logic(
        self,
        data: FloatDataType,
        factor: float,
        from_ctx: float,
        defaulted: float = 3.0,
    ) -> FloatDataType:
        return FloatDataType((data.data * factor) + from_ctx + defaulted)


def test_param_provenance(tmp_path: Path) -> None:
    pipeline_spec = [{"processor": ParamOp, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType({"from_ctx": 5.0}))
    trace_path = tmp_path / "trace.ser.jsonl"
    trace = JSONLTrace(str(trace_path))
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=pipeline_spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=trace,
    )
    trace.close()
    ser = next(
        json.loads(line)
        for line in trace_path.read_text().splitlines()
        if line and json.loads(line).get("type") == "ser"
    )
    action = ser["action"]
    assert action["params"] == {"factor": 2.0, "from_ctx": 5.0, "defaulted": 3.0}
    assert action["param_source"] == {
        "factor": "node",
        "from_ctx": "context",
        "defaulted": "default",
    }
