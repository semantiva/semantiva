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

"""Typed registry for Semantiva pipeline processors and related classes."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence, Set
import importlib
import inspect

from semantiva.logger import Logger
from semantiva.context_processors.context_processors import ContextProcessor
from semantiva.data_processors.data_processors import _BaseDataProcessor
from semantiva.data_io.data_io import DataSource, DataSink, PayloadSource, PayloadSink
from semantiva.data_types.data_types import DataCollectionType
from semantiva.workflows.fitting_model import FittingModel


class ProcessorRegistry:
    """Central registry mapping canonical names to processor classes.

    The registry stores concrete subclasses of :class:`ContextProcessor`,
    :class:`~semantiva.data_processors.data_processors._BaseDataProcessor`,
    :class:`~semantiva.data_io.data_io.DataSource`,
    :class:`~semantiva.data_types.data_types.DataCollectionType`, and
    :class:`~semantiva.workflows.fitting_model.FittingModel`.

    Modules are imported eagerly when registered to trigger component
    registration via metaclasses and to allow inspection of public classes.
    Multiple registrations are idempotent: later imports simply refresh the
    stored mapping.
    """

    _processors: Dict[str, type[Any]] = {}
    _registered_modules: Set[str] = set()
    _module_history: list[str] = []
    _defaults_loaded: bool = False
    _logger = Logger()

    _ALLOWED_BASES: tuple[type, ...] = (
        ContextProcessor,
        _BaseDataProcessor,
        DataSource,
        DataSink,
        PayloadSource,
        PayloadSink,
        DataCollectionType,
        FittingModel,
    )

    @classmethod
    def clear(cls) -> None:
        """Reset the registry (primarily for tests)."""

        cls._processors.clear()
        cls._registered_modules.clear()
        cls._module_history.clear()

        # Also reset extension loading tracking to allow re-loading extensions
        from . import plugin_registry

        plugin_registry._LOADED_EXTENSIONS.clear()
        cls._defaults_loaded = False

    @classmethod
    def register_processor(cls, name: str, proc_cls: type[Any]) -> None:
        """Register a processor class under a canonical name."""

        if not isinstance(name, str) or not name:
            raise ValueError("Processor name must be a non-empty string")
        if not isinstance(proc_cls, type):
            raise TypeError("proc_cls must be a type")
        cls._processors[name] = proc_cls

    @classmethod
    def register_modules(cls, modules: Iterable[str] | str) -> None:
        """Import modules and register eligible processor classes."""

        if isinstance(modules, str):
            modules = [modules]

        for module_name in modules:
            if module_name in cls._registered_modules:
                continue
            cls._registered_modules.add(module_name)
            cls._module_history.append(module_name)
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:  # pragma: no cover - graceful logging path
                cls._logger.warning(
                    "Failed to import module '%s': %s", module_name, exc
                )
                continue

            for attr_name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue
                if any(issubclass(obj, base) for base in cls._ALLOWED_BASES):
                    cls._processors[attr_name] = obj

    @classmethod
    def get_processor(cls, name: str) -> type[Any]:
        """Retrieve a registered processor class by name."""
        try:
            return cls._processors[name]
        except KeyError as exc:  # pragma: no cover - handled by resolve_symbol
            raise KeyError(f"Unknown processor '{name}'") from exc

    @classmethod
    def all_processors(cls) -> Dict[str, type[Any]]:
        """Return dictionary of all registered processors."""
        return dict(cls._processors)

    @classmethod
    def registered_modules(cls) -> Set[str]:
        """Return set of module names that have been registered."""
        return set(cls._registered_modules)

    @classmethod
    def module_history(cls) -> Sequence[str]:
        """Return ordered list of all registered module names."""
        return list(cls._module_history)

    @classmethod
    def ensure_default_modules(cls, modules: Iterable[str]) -> None:
        """Register default modules if not already loaded."""
        if not cls._defaults_loaded or not cls._processors:
            cls.register_modules(modules)
            cls._defaults_loaded = True
