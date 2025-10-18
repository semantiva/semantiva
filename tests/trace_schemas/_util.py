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
from typing import Mapping

import jsonschema
from referencing import Registry
from referencing.jsonschema import SchemaResource

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "semantiva" / "trace" / "schema"


def load_json(relpath: str) -> dict:
    return json.loads((ROOT / relpath).read_text(encoding="utf-8"))


def schema(relpath: str) -> dict:
    return load_json(relpath)


def _build_registry() -> Registry:
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        uri = contents.get("$id")
        if not isinstance(uri, str):
            continue
        resource = SchemaResource.from_contents(contents)
        registry = registry.with_resource(uri, resource)
    return registry


_REGISTRY = _build_registry()


def validator(relpath: str) -> jsonschema.validators.Draft202012Validator:
    contents = load_json(relpath)
    return jsonschema.validators.Draft202012Validator(contents, registry=_REGISTRY)


def validate(instance: Mapping[str, object], relpath: str) -> None:
    validator(relpath).validate(instance)
