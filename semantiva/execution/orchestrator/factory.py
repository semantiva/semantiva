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
"""Factory utilities for constructing orchestrators from configuration."""

from __future__ import annotations

from typing import Any, Dict

from semantiva.configurations.schema import ExecutionConfig
from ..component_registry import ExecutionComponentRegistry


def _instantiate_if_present(name: str | None, component_type: str) -> Any | None:
    if not name:
        return None

    try:
        if component_type == "orchestrator":
            cls = ExecutionComponentRegistry.get_orchestrator(name)
        elif component_type == "executor":
            cls = ExecutionComponentRegistry.get_executor(name)
        elif component_type == "transport":
            cls = ExecutionComponentRegistry.get_transport(name)
        else:  # pragma: no cover - defensive guard
            raise ValueError(f"Unknown component type: {component_type}")
    except KeyError as exc:
        raise ValueError(f"Unknown {component_type}: {name}") from exc

    return cls()


def _attempt_construct(cls: type, kwargs: Dict[str, Any]) -> Any:
    attempt_order = [
        dict(kwargs),
        {k: v for k, v in kwargs.items() if k != "options"},
        {k: v for k, v in kwargs.items() if k not in {"options", "transport"}},
        {
            k: v
            for k, v in kwargs.items()
            if k not in {"options", "transport", "executor"}
        },
        {},
    ]
    last_error: Exception | None = None
    for candidate in attempt_order:
        try:
            return cls(**candidate)
        except TypeError as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    return cls()


def build_orchestrator(
    exec_cfg: ExecutionConfig,
    *,
    transport: Any | None = None,
    executor: Any | None = None,
):
    """Construct an orchestrator respecting explicit transport and executor.

    This factory function uses the ExecutionComponentRegistry to resolve orchestrator,
    executor, and transport classes by name, then constructs them with dependency
    injection. It provides graceful fallbacks for constructor argument compatibility.

    Args:
        exec_cfg: Execution configuration containing component names and options
        transport: Optional transport instance to inject (overrides config)
        executor: Optional executor instance to inject (overrides config)

    Returns:
        Configured orchestrator instance with injected dependencies

    Raises:
        ValueError: If specified component names are not found in registry
        TypeError: If component construction fails with all argument combinations

    Example:
        >>> from semantiva.configurations.schema import ExecutionConfig
        >>> config = ExecutionConfig(orchestrator="LocalSemantivaOrchestrator")
        >>> orchestrator = build_orchestrator(config)
    """

    transport_obj = transport or _instantiate_if_present(
        exec_cfg.transport, "transport"
    )
    executor_obj = executor or _instantiate_if_present(exec_cfg.executor, "executor")

    if exec_cfg.orchestrator:
        try:
            orch_cls = ExecutionComponentRegistry.get_orchestrator(
                exec_cfg.orchestrator
            )
        except KeyError as exc:
            raise ValueError(f"Unknown orchestrator: {exec_cfg.orchestrator}") from exc
    else:
        from .orchestrator import LocalSemantivaOrchestrator

        orch_cls = LocalSemantivaOrchestrator

    kwargs: Dict[str, Any] = {}
    if transport_obj is not None:
        kwargs["transport"] = transport_obj
    if executor_obj is not None:
        kwargs["executor"] = executor_obj
    if exec_cfg.options:
        kwargs["options"] = exec_cfg.options

    orchestrator = _attempt_construct(orch_cls, kwargs)
    return orchestrator


__all__ = ["build_orchestrator"]
