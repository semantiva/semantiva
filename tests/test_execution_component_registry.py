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

"""Tests for the execution component registry helper utilities."""

from __future__ import annotations

import pytest

from semantiva.execution.component_registry import (
    ExecutionComponentRegistry as ECR,
)


@pytest.fixture()
def restore_registry():
    """Snapshot registry state and restore after each test."""

    original_orchestrators = ECR.get_registered_orchestrators()
    original_executors = ECR.get_registered_executors()
    original_transports = ECR.get_registered_transports()
    original_initialized = ECR._initialized  # type: ignore[attr-defined]
    ECR.clear()
    try:
        yield
    finally:
        ECR.clear()
        for name, cls in original_orchestrators.items():
            ECR.register_orchestrator(name, cls)
        for name, cls in original_executors.items():
            ECR.register_executor(name, cls)
        for name, cls in original_transports.items():
            ECR.register_transport(name, cls)
        ECR._initialized = original_initialized  # type: ignore[attr-defined]


def test_ecr_lists_and_gets_roundtrip(restore_registry):
    class DummyOrchestrator:
        pass

    class DummyExecutor:
        pass

    class DummyTransport:
        pass

    ECR.register_orchestrator("dummy_orch", DummyOrchestrator)
    ECR.register_executor("dummy_exec", DummyExecutor)
    ECR.register_transport("dummy_tx", DummyTransport)

    assert ECR.get_orchestrator("dummy_orch") is DummyOrchestrator
    assert ECR.get_executor("dummy_exec") is DummyExecutor
    assert ECR.get_transport("dummy_tx") is DummyTransport

    assert ECR.list_orchestrators() == ["dummy_orch"]
    assert ECR.list_executors() == ["dummy_exec"]
    assert ECR.list_transports() == ["dummy_tx"]

    with pytest.raises(KeyError):
        ECR.get_executor("missing")


def test_initialize_defaults_registers_aliases(restore_registry):
    ECR.initialize_defaults()
    assert "local" in ECR.list_orchestrators()
    assert "sequential" in ECR.list_executors()
    assert "in_memory" in ECR.list_transports()
