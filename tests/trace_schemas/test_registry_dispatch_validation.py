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

from typing import Mapping, cast

import pytest

try:  # pragma: no cover - optional dependency
    import jsonschema
except Exception:  # pragma: no cover - optional dependency
    jsonschema = None
    pytest.skip("jsonschema not installed", allow_module_level=True)

from ._util import schema, validator

HEADER = validator("semantiva/trace/schema/trace_header_v1.schema.json")
REGISTRY = schema("semantiva/trace/schema/trace_registry_v1.json")


def _lookup_schema(record_type: str) -> jsonschema.validators.Draft202012Validator:
    url = REGISTRY["records"].get(record_type)
    assert url, f"Unknown record_type: {record_type}"
    name = url.rsplit("/", 1)[-1]
    return validator(f"semantiva/trace/schema/{name}")


def _validate(obj: Mapping[str, object]) -> None:
    HEADER.validate(obj)
    # mypy cannot infer the runtime type of obj["record_type"]; cast to str
    record_type = cast(str, obj["record_type"])
    record_schema = _lookup_schema(record_type)
    record_schema.validate(obj)


def test_dispatch_over_samples() -> None:
    start = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "run_id": "run-1",
        "pipeline_id": "plid-1",
        "pipeline_spec_canonical": {"nodes": [], "edges": [], "version": 1},
    }
    ser = {
        "record_type": "ser",
        "schema_version": 1,
        "run_id": "run-1",
        "identity": {
            "run_id": "run-1",
            "pipeline_id": "plid-1",
            "node_id": "node-1",
        },
        "dependencies": {"upstream": []},
        "processor": {
            "ref": "example.Processor",
            "parameters": {},
            "parameter_sources": {},
        },
        "context_delta": {
            "read_keys": [],
            "created_keys": [],
            "updated_keys": [],
            "key_summaries": {},
        },
        "assertions": {
            "preconditions": [{"code": "pre:ok", "result": "PASS"}],
            "postconditions": [{"code": "post:ok", "result": "PASS"}],
            "invariants": [],
            "environment": {
                "python": "3.12",
                "platform": "linux-x86_64",
                "semantiva": "0.5.0",
            },
            "redaction_policy": {},
        },
        "timing": {
            "started_at": "2025-01-01T00:00:00Z",
            "finished_at": "2025-01-01T00:00:01Z",
            "wall_ms": 1000,
            "cpu_ms": 500,
        },
        "status": "succeeded",
    }
    end = {
        "record_type": "pipeline_end",
        "schema_version": 1,
        "run_id": "run-1",
        "summary": {"status": "ok"},
    }

    for obj in (start, ser, end):
        _validate(obj)


def test_unknown_record_type_fails_lookup() -> None:
    bad = {"record_type": "mystery", "schema_version": 1, "run_id": "run-1"}
    HEADER.validate(bad)
    with pytest.raises(AssertionError):
        _lookup_schema(cast(str, bad["record_type"]))
