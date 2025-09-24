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

"""Tests for deterministic extension loading."""

from __future__ import annotations

import sys
import types

import pytest

from semantiva.execution.component_registry import ExecutionComponentRegistry as ECR
from semantiva.registry import plugin_registry


@pytest.fixture(autouse=True)
def reset_plugin_registry(monkeypatch):
    """Ensure a fresh extension loader state for each test."""

    monkeypatch.setattr(plugin_registry, "_LOADED_EXTENSIONS", set())
    yield


@pytest.fixture()
def clear_ecr():
    original = (
        ECR.get_registered_orchestrators(),
        ECR.get_registered_executors(),
        ECR.get_registered_transports(),
        ECR._initialized,  # type: ignore[attr-defined]
    )
    ECR.clear()
    try:
        yield
    finally:
        ECR.clear()
        for name, cls in original[0].items():
            ECR.register_orchestrator(name, cls)
        for name, cls in original[1].items():
            ECR.register_executor(name, cls)
        for name, cls in original[2].items():
            ECR.register_transport(name, cls)
        ECR._initialized = original[3]  # type: ignore[attr-defined]


def test_load_extension_from_module_register(monkeypatch, clear_ecr):
    module_name = "ext_mod_demo"
    registration_calls = []

    mod = types.ModuleType(module_name)

    def _register() -> None:
        registration_calls.append(1)

        class _DummyExec:
            pass

        ECR.register_executor("demo", _DummyExec)

    mod.register = _register  # type: ignore[attr-defined]
    sys.modules[module_name] = mod

    try:
        plugin_registry.load_extensions([module_name])
        plugin_registry.load_extensions([module_name])
    finally:
        sys.modules.pop(module_name, None)

    assert registration_calls == [1]
    assert "demo" in ECR.list_executors()


def test_load_extension_missing(monkeypatch):
    with pytest.raises(RuntimeError, match="Could not load extensions"):
        plugin_registry.load_extensions(["does_not_exist_extension"])
