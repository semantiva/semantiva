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

from typing import Any, Dict, Optional, Tuple, List, Set
import inspect

from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT
from semantiva.context_processors.context_types import ContextType


_RESERVED_NAMES: Set[str] = {"context"}


def _allowed_param_names(processor_cls) -> Set[str]:
    """Introspect `_process_logic` and return allowed parameter names.

    Allowed names exclude framework-reserved names.
    Processors with **kwargs are rejected for provenance reliability,
    except for certain factory-generated classes that need dynamic parameters.
    """

    fn = getattr(processor_cls, "_process_logic", None)
    if fn is None:
        return set()
    sig = inspect.signature(fn)
    names: Set[str] = set()

    # Check for **kwargs
    has_kwargs = any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )

    if has_kwargs:
        # Allow **kwargs for specific factory-generated classes that need dynamic parameters
        class_name = processor_cls.__name__
        allowed_kwargs_patterns = [
            "ParametricSweep",  # Parametric sweep factory
            # Add other dynamic processor patterns as needed
        ]

        is_allowed_dynamic = any(
            pattern in class_name for pattern in allowed_kwargs_patterns
        )

        if not is_allowed_dynamic:
            raise ValueError(
                f"Processor {processor_cls.__name__} uses **kwargs which is incompatible "
                f"with reliable provenance tracking. All parameters must be explicitly declared."
            )

    for p in sig.parameters.values():
        if p.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            if p.name not in _RESERVED_NAMES:
                names.add(p.name)
    return names


def classify_unknown_config_params(
    *,
    processor_cls,
    processor_config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return list of issues for unknown configuration parameters.

    Each issue is structured as::

        {
            "name": <param>,
            "reason": "unknown_parameter",
        }

    Processors using **kwargs are generally rejected for provenance reliability,
    except for specific factory-generated classes. For allowed **kwargs processors,
    no issues are reported as parameters are passed through dynamically.
    """

    # Check if processor has **kwargs
    fn = getattr(processor_cls, "_process_logic", None)
    if fn is not None:
        sig = inspect.signature(fn)
        has_kwargs = any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )

        if has_kwargs:
            # Check if this is an allowed **kwargs processor
            class_name = processor_cls.__name__
            allowed_kwargs_patterns = [
                "ParametricSweep",  # Parametric sweep factory
                # Add other dynamic processor patterns as needed
            ]

            is_allowed_dynamic = any(
                pattern in class_name for pattern in allowed_kwargs_patterns
            )

            if is_allowed_dynamic:
                # For allowed dynamic processors, don't validate parameters
                return []

    allowed = _allowed_param_names(processor_cls)
    extras = [k for k in processor_config.keys() if k not in allowed]
    issues: List[Dict[str, Any]] = []
    for name in extras:
        issues.append(
            {
                "name": name,
                "reason": "unknown_parameter",
            }
        )
    return issues


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
