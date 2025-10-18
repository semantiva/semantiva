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

import jsonschema
from importlib import resources


SCHEMA_PATH = (
    resources.files("semantiva.trace.schema")
    / "semantic_execution_record_v1.schema.json"
)
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
validate = jsonschema.Draft202012Validator(SCHEMA).validate


def test_ser_without_cpu_ms_is_valid() -> None:
    rec = {
        "record_type": "ser",
        "schema_version": 1,
        "identity": {"run_id": "r", "pipeline_id": "p", "node_id": "n"},
        "dependencies": {"upstream": []},
        "processor": {"ref": "x", "parameters": {}, "parameter_sources": {}},
        "context_delta": {
            "read_keys": [],
            "created_keys": [],
            "updated_keys": [],
            "key_summaries": {},
        },
        "assertions": {
            "preconditions": [{"code": "noop", "result": "PASS"}],
            "postconditions": [{"code": "noop", "result": "PASS"}],
            "invariants": [],
            "environment": {"python": "3.12", "platform": "linux", "semantiva": "x"},
            "redaction_policy": {},
        },
        "timing": {
            "started_at": "2025-01-01T00:00:00Z",
            "finished_at": "2025-01-01T00:00:00Z",
            "wall_ms": 10,
        },
        "status": "succeeded",
    }
    validate(rec)


def test_ser_with_cpu_ms_is_valid() -> None:
    rec = {
        "record_type": "ser",
        "schema_version": 1,
        "identity": {"run_id": "r", "pipeline_id": "p", "node_id": "n"},
        "dependencies": {"upstream": []},
        "processor": {"ref": "x", "parameters": {}, "parameter_sources": {}},
        "context_delta": {
            "read_keys": [],
            "created_keys": [],
            "updated_keys": [],
            "key_summaries": {},
        },
        "assertions": {
            "preconditions": [{"code": "noop", "result": "PASS"}],
            "postconditions": [{"code": "noop", "result": "PASS"}],
            "invariants": [],
            "environment": {"python": "3.12", "platform": "linux", "semantiva": "x"},
            "redaction_policy": {},
        },
        "timing": {
            "started_at": "2025-01-01T00:00:00Z",
            "finished_at": "2025-01-01T00:00:00Z",
            "wall_ms": 10,
            "cpu_ms": 7,
        },
        "status": "succeeded",
    }
    validate(rec)
