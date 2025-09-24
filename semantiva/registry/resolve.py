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

"""Public entry point for resolving processor symbols."""

from __future__ import annotations

import importlib
from typing import Type, Union

from .bootstrap import DEFAULT_MODULES
from .name_resolver_registry import NameResolverRegistry
from .processor_registry import ProcessorRegistry


def _ensure_defaults_loaded() -> None:
    ProcessorRegistry.ensure_default_modules(DEFAULT_MODULES)


class UnknownProcessorError(LookupError):
    """Raised when a processor symbol cannot be resolved."""


def resolve_symbol(name_or_type: Union[str, Type]) -> Type:
    """Resolve a processor symbol to a concrete class.

    Strings are processed in three phases:
    1. Prefix-based name resolvers (``rename:``, ``delete:``, etc.)
    2. Registered processors via :class:`ProcessorRegistry`
    3. Fully qualified ``module:Class`` imports (auto-registered on success)
    """

    if isinstance(name_or_type, type):
        return name_or_type

    symbol = str(name_or_type)

    _ensure_defaults_loaded()

    resolved = NameResolverRegistry.resolve(symbol)
    if resolved is not None:
        return resolved

    try:
        return ProcessorRegistry.get_processor(symbol)
    except KeyError:
        pass

    if ":" in symbol:
        module_name, _, class_name = symbol.partition(":")
        if "." in module_name:
            module = importlib.import_module(module_name)
            candidate = getattr(module, class_name)
            if isinstance(candidate, type):
                ProcessorRegistry.register_processor(class_name, candidate)
                return candidate

    raise UnknownProcessorError(f"Cannot resolve processor symbol: {symbol!r}")
