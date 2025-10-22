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

"""Parameter resolver registry for structured configuration values."""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional

Resolver = Callable[[Any], Optional[Any]]


class ParameterResolverRegistry:
    """Maintain ordered parameter resolvers and provide recursive resolution."""

    _resolvers: List[Resolver] = []
    _builtin_names: set[str] = set()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parameter resolvers."""
        cls._resolvers.clear()
        cls._builtin_names.clear()

    @classmethod
    def register_resolver(cls, resolver_fn: Resolver, *, builtin: bool = False) -> None:
        """Register a parameter resolver function with optional builtin flag."""
        if resolver_fn not in cls._resolvers:
            cls._resolvers.append(resolver_fn)
        if builtin:
            cls._builtin_names.add(getattr(resolver_fn, "__name__", str(resolver_fn)))

    @classmethod
    def resolvers(cls) -> Iterable[Resolver]:
        """Return a copy of all registered resolver functions."""
        return list(cls._resolvers)

    @classmethod
    def builtin_names(cls) -> set[str]:
        """Return set of builtin resolver function names."""
        return set(cls._builtin_names)


def resolve_parameters(obj: Any) -> Any:
    """Recursively resolve values using registered parameter resolvers."""

    if isinstance(obj, dict):
        return {k: resolve_parameters(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_parameters(item) for item in obj]
    if isinstance(obj, str):
        for resolver in ParameterResolverRegistry.resolvers():
            resolved = resolver(obj)
            if resolved is not None:
                return resolved
        return obj
    return obj
