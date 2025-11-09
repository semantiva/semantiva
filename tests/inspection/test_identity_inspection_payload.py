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

"""Tests for deterministic inspection payload identities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from semantiva.inspection.builder import build, build_pipeline_inspection
from semantiva.registry.processor_registry import ProcessorRegistry


def _load_payload(yaml_path: Path) -> Any:
    ProcessorRegistry.register_modules("semantiva.examples.test_utils")
    config = yaml.safe_load(yaml_path.read_text())
    nodes = config.get("pipeline", {}).get("nodes", [])
    inspection = build_pipeline_inspection(nodes)
    return build(config, inspection=inspection)


def test_inspection_payload_shape() -> None:
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    payload = _load_payload(yaml_path)

    assert "identity" in payload
    identity = payload["identity"]
    assert isinstance(identity, dict)
    assert str(identity.get("semantic_id", "")).startswith("plsemid-")
    assert str(identity.get("config_id", "")).startswith("plcid-")

    forbidden = [
        "run_id",
        "pipeline_id",
        "run_space_launch_id",
        "run_space_attempt",
        "run_space_index",
        "run_space_context",
        "run_space_inputs_id",
    ]
    blob = json.dumps(payload)
    for key in forbidden:
        assert key not in blob


def test_semantic_and_config_determinism() -> None:
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    payload_a = _load_payload(yaml_path)
    payload_b = _load_payload(yaml_path)

    assert payload_a["identity"]["semantic_id"] == payload_b["identity"]["semantic_id"]
    assert payload_a["identity"]["config_id"] == payload_b["identity"]["config_id"]


def test_sanitize_sweep_never_exposes_raw_expr() -> None:
    yaml_path = Path("tests/parametric_sweep_demo.yaml")
    payload = _load_payload(yaml_path)
    text = json.dumps(payload)
    assert "expr:" not in text
    assert "preprocessor_view" not in text
