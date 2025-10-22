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

"""Registry for name-based processor resolvers."""

from __future__ import annotations

from typing import Callable, Dict, Optional, Type

Resolver = Callable[[str], Optional[Type]]


class NameResolverRegistry:
    """Store and apply prefix-based name resolvers."""

    _resolvers: Dict[str, Resolver] = {}

    @classmethod
    def clear(cls) -> None:
        """Clear all registered name resolvers."""
        cls._resolvers.clear()

    @classmethod
    def register_resolver(cls, prefix: str, fn: Resolver) -> None:
        """Register a name resolver function for a given prefix."""
        if not prefix or not prefix.endswith(":"):
            raise ValueError(
                "Resolver prefix must be a non-empty string ending with ':'"
            )
        cls._resolvers[prefix] = fn

    @classmethod
    def resolve(cls, value: str) -> Optional[Type]:
        """Attempt to resolve a string value using registered prefix resolvers."""
        for prefix, fn in cls._resolvers.items():
            if value.startswith(prefix):
                resolved = fn(value)
                if resolved is not None:
                    return resolved
        return None

    @classmethod
    def all_resolvers(cls) -> Dict[str, Resolver]:
        """Return dictionary of all registered name resolvers."""
        return dict(cls._resolvers)
