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

import pytest

try:  # pragma: no cover - optional dependency
    import jsonschema
except Exception:  # pragma: no cover - optional dependency
    jsonschema = None
    pytest.skip("jsonschema not installed", allow_module_level=True)

from ._util import schema

HEADER = schema("semantiva/trace/schema/trace_header_v1.schema.json")
END = schema("semantiva/trace/schema/pipeline_end_event_v1.schema.json")


def test_pipeline_end_ok() -> None:
    obj = {
        "record_type": "pipeline_end",
        "schema_version": 1,
        "run_id": "run-abc",
        "summary": {"status": "ok"},
    }
    jsonschema.validate(obj, HEADER)
    jsonschema.validate(obj, END)


def test_pipeline_end_requires_run_id() -> None:
    bad = {"record_type": "pipeline_end", "schema_version": 1}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, HEADER)


def test_pipeline_end_wrong_record_type_fails() -> None:
    bad = {"record_type": "end", "schema_version": 1, "run_id": "run-abc"}
    jsonschema.validate(bad, HEADER)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, END)
