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
"""Helpers for expanding declarative fan-out specifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from semantiva.configurations.schema import FanoutSpec
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError as ConfigurationError,
)


def _sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _load_values_file(path: Path) -> tuple[Any, str]:
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:  # pragma: no cover - path errors bubble up
        raise ConfigurationError(f"fanout values file not found: {path}") from exc
    if path.suffix.lower() == ".json":
        payload = json.loads(data.decode("utf-8"))
    else:
        payload = yaml.safe_load(data)  # type: ignore[no-untyped-call]
    return payload, _sha256_bytes(data)


def expand_fanout(
    spec: FanoutSpec,
    *,
    cwd: str | Path = ".",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Expand ``FanoutSpec`` into per-run context injections and metadata."""

    meta: Dict[str, Any] = {}
    payload: Any = None
    base_path = Path(cwd)

    if spec.values_file:
        payload, sha = _load_values_file(base_path / spec.values_file)
        meta["source_file"] = spec.values_file
        meta["source_sha256"] = sha

    # Single parameter fan-out -------------------------------------------------
    if spec.param:
        values = spec.values if spec.values is not None else payload
        if values is None:
            raise ConfigurationError(
                "fanout.param requires 'values' or 'values_file' to provide a list"
            )
        if not isinstance(values, list):
            raise ConfigurationError(
                "fanout.values (or loaded values_file) must be a list for single-param fan-out"
            )
        runs = [{spec.param: value} for value in values]
        meta["mode"] = "single"
        return runs, meta

    # Multi parameter fan-out --------------------------------------------------
    multi_spec: Dict[str, List[Any]] = {}
    if spec.multi:
        multi_spec.update(spec.multi)
    elif isinstance(payload, dict):
        multi_spec.update(payload)

    if not multi_spec:
        meta["mode"] = "none"
        return [], meta

    lengths = {key: len(value) for key, value in multi_spec.items()}
    if len(set(lengths.values())) != 1:
        raise ConfigurationError(
            "fanout.multi lists must have identical size; got lengths " + str(lengths)
        )
    count = next(iter(lengths.values())) if lengths else 0
    runs_multi: List[Dict[str, Any]] = []
    for index in range(count):
        runs_multi.append({key: multi_spec[key][index] for key in multi_spec})

    meta["mode"] = "multi_zip"
    return runs_multi, meta


__all__ = ["expand_fanout"]
