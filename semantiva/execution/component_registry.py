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

"""Execution Component Registry for orchestrators, executors, and transports.

This module provides a registry specifically for execution components to avoid
circular import dependencies with the main ProcessorRegistry and graph builder modules.
The registry follows the dependency inversion principle by being a dependency sink
rather than creating webs of interdependence.
"""

from __future__ import annotations

from typing import Dict, List, Type

from semantiva.logger import Logger


class ExecutionComponentRegistry:
    """Registry for execution layer components: orchestrators, executors, transports.

    This registry is designed to break circular import dependencies by providing
    a dedicated registration system for execution components that doesn't depend
    on graph building or general class resolution functionality.
    """

    _orchestrators: Dict[str, Type] = {}
    _executors: Dict[str, Type] = {}
    _transports: Dict[str, Type] = {}
    _initialized: bool = False

    @classmethod
    def register_orchestrator(cls, name: str, orchestrator_cls: Type) -> None:
        """Register an orchestrator class by name.

        Args:
            name: String identifier for the orchestrator
            orchestrator_cls: The orchestrator class to register
        """
        cls._orchestrators[name] = orchestrator_cls
        Logger().debug(f"Registered orchestrator: {name}")

    @classmethod
    def register_executor(cls, name: str, executor_cls: Type) -> None:
        """Register an executor class by name.

        Args:
            name: String identifier for the executor
            executor_cls: The executor class to register
        """
        cls._executors[name] = executor_cls
        Logger().debug(f"Registered executor: {name}")

    @classmethod
    def register_transport(cls, name: str, transport_cls: Type) -> None:
        """Register a transport class by name.

        Args:
            name: String identifier for the transport
            transport_cls: The transport class to register
        """
        cls._transports[name] = transport_cls
        Logger().debug(f"Registered transport: {name}")

    @classmethod
    def get_orchestrator(cls, name: str) -> Type:
        """Get an orchestrator class by name.

        Args:
            name: String identifier for the orchestrator

        Returns:
            The orchestrator class registered under ``name``.

        Raises:
            KeyError: If no orchestrator is registered under ``name``.
        """

        try:
            return cls._orchestrators[name]
        except KeyError as exc:  # pragma: no cover - exercised via CLI helpers
            raise KeyError(name) from exc

    @classmethod
    def get_executor(cls, name: str) -> Type:
        """Get an executor class by name.

        Args:
            name: String identifier for the executor

        Returns:
            The executor class registered under ``name``.

        Raises:
            KeyError: If no executor is registered under ``name``.
        """

        try:
            return cls._executors[name]
        except KeyError as exc:  # pragma: no cover - exercised via CLI helpers
            raise KeyError(name) from exc

    @classmethod
    def get_transport(cls, name: str) -> Type:
        """Get a transport class by name.

        Args:
            name: String identifier for the transport

        Returns:
            The transport class registered under ``name``.

        Raises:
            KeyError: If no transport is registered under ``name``.
        """

        try:
            return cls._transports[name]
        except KeyError as exc:  # pragma: no cover - exercised via CLI helpers
            raise KeyError(name) from exc

    @classmethod
    def initialize_defaults(cls) -> None:
        """Initialize default execution components.

        This method registers the built-in orchestrators, executors, and transports.
        It's designed to be called after other modules are loaded to avoid circular
        import issues.

        Safe to call multiple times - subsequent calls are idempotent.
        """
        if cls._initialized:
            return

        # Import here to avoid circular dependencies
        from .orchestrator.orchestrator import (
            LocalSemantivaOrchestrator,
            SemantivaOrchestrator,
        )
        from .executor.executor import SequentialSemantivaExecutor
        from .transport import InMemorySemantivaTransport

        # Register default orchestrators
        cls.register_orchestrator(
            "LocalSemantivaOrchestrator", LocalSemantivaOrchestrator
        )
        cls.register_orchestrator("SemantivaOrchestrator", SemantivaOrchestrator)
        cls.register_orchestrator("local", LocalSemantivaOrchestrator)

        # Register default executors
        cls.register_executor(
            "SequentialSemantivaExecutor", SequentialSemantivaExecutor
        )
        cls.register_executor("sequential", SequentialSemantivaExecutor)

        # Register default transports
        cls.register_transport("InMemorySemantivaTransport", InMemorySemantivaTransport)
        cls.register_transport("in_memory", InMemorySemantivaTransport)

        cls._initialized = True
        Logger().debug("ExecutionComponentRegistry initialized with defaults")

    @classmethod
    def get_registered_orchestrators(cls) -> Dict[str, Type]:
        """Get all registered orchestrators."""
        return dict(cls._orchestrators)

    @classmethod
    def get_registered_executors(cls) -> Dict[str, Type]:
        """Get all registered executors."""
        return dict(cls._executors)

    @classmethod
    def get_registered_transports(cls) -> Dict[str, Type]:
        """Get all registered transports."""
        return dict(cls._transports)

    @classmethod
    def list_orchestrators(cls) -> List[str]:
        """Return orchestrator identifiers in sorted order."""

        return sorted(cls._orchestrators.keys())

    @classmethod
    def list_executors(cls) -> List[str]:
        """Return executor identifiers in sorted order."""

        return sorted(cls._executors.keys())

    @classmethod
    def list_transports(cls) -> List[str]:
        """Return transport identifiers in sorted order."""

        return sorted(cls._transports.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered components. Primarily for testing."""
        cls._orchestrators.clear()
        cls._executors.clear()
        cls._transports.clear()
        cls._initialized = False


__all__ = ["ExecutionComponentRegistry"]
