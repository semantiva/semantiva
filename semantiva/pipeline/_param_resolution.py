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

"""
Single source of truth for parameter resolution.

Provides unified parameter resolution policy (config > context > defaults)
for both runtime execution and inspection classification across all processors.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT
from semantiva.context_processors.context_types import ContextType


def _default_for(processor_cls, name: str):
    meta = processor_cls.get_metadata()
    pinfo = meta.get("parameters", {}).get(name)
    if isinstance(pinfo, ParameterInfo):
        return pinfo.default
    if isinstance(pinfo, dict):
        return pinfo.get("default", _NO_DEFAULT)
    return _NO_DEFAULT


def resolve_runtime_value(
    *,
    name: str,
    processor_cls,
    processor_config: Dict[str, Any],
    context: ContextType,
) -> Any:
    """Single source of truth for runtime resolution: config > context > default."""
    if name in processor_config:
        return processor_config[name]
    if name in context.keys():
        return context.get_value(name)
    d = _default_for(processor_cls, name)
    if d is not _NO_DEFAULT:
        return d
    raise KeyError(
        f"Unable to resolve parameter '{name}' from context, node configuration, or defaults."
    )


def inspect_origin(
    *,
    name: str,
    processor_cls,
    processor_config: Dict[str, Any],
    key_origin: Dict[str, int],
    deleted_keys: set[str],
) -> Tuple[str, Optional[int], Optional[Any]]:
    """
    Classification for inspection (no values available during inspect):

    Returns (origin, origin_idx, default_value_if_any)
    origin ∈ {'config','context','default','required'}
    """
    if name in processor_config:
        return "config", None, None
    if name in key_origin and name not in deleted_keys:
        return "context", key_origin.get(name), None
    d = _default_for(processor_cls, name)
    if d is not _NO_DEFAULT:
        return "default", None, d
    return "required", None, None
