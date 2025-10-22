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

"""Built-in name and parameter resolvers for Semantiva."""

from __future__ import annotations

import importlib
import re
from typing import Any, Optional, Type, cast

from semantiva.context_processors.factory import (
    _context_deleter_factory,
    _context_renamer_factory,
    _context_template_factory,
)
from semantiva.data_processors.data_processors import _BaseDataProcessor
from semantiva.data_processors.data_slicer_factory import slice
from semantiva.data_types.data_types import DataCollectionType
from semantiva.workflows.fitting_model import FittingModel

from .bootstrap import DEFAULT_MODULES
from .descriptors import ModelDescriptor
from .name_resolver_registry import NameResolverRegistry
from .parameter_resolver_registry import ParameterResolverRegistry
from .processor_registry import ProcessorRegistry


_RE_RENAME = re.compile(r"^rename:(?P<src>.+?):(?P<dst>.+)$")
_RE_DELETE = re.compile(r"^delete:(?P<key>.+)$")
_RE_TEMPLATE = re.compile(
    r"^template:(?P<quote>\"|')(?P<template>.*?)(?P=quote):(?P<out>[A-Za-z_][A-Za-z0-9_.]*)$"
)
_RE_SLICE = re.compile(
    r"^slice:(?P<proc>[A-Za-z_][A-Za-z0-9_]*):(?P<collection>[A-Za-z_][A-Za-z0-9_]*)$"
)


def _resolve_rename(value: str) -> Optional[Type]:
    match = _RE_RENAME.match(value)
    if not match:
        return None
    return _context_renamer_factory(match.group("src"), match.group("dst"))


def _resolve_delete(value: str) -> Optional[Type]:
    match = _RE_DELETE.match(value)
    if not match:
        return None
    return _context_deleter_factory(match.group("key"))


def _resolve_template(value: str) -> Optional[Type]:
    match = _RE_TEMPLATE.match(value)
    if not match:
        return None
    return _context_template_factory(
        template=match.group("template"), output_key=match.group("out")
    )


def _resolve_slice(value: str) -> Optional[Type]:
    match = _RE_SLICE.match(value)
    if not match:
        return None
    processor_cls = cast(
        type[_BaseDataProcessor],
        ProcessorRegistry.get_processor(match.group("proc")),
    )
    collection_cls = cast(
        type[DataCollectionType],
        ProcessorRegistry.get_processor(match.group("collection")),
    )
    if not issubclass(processor_cls, _BaseDataProcessor):
        raise ValueError(f"{processor_cls.__name__} is not a data processor")
    if not issubclass(collection_cls, DataCollectionType):
        raise ValueError(f"{collection_cls.__name__} is not a DataCollectionType")
    return slice(processor_cls, collection_cls)


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    for caster in (int, float):
        try:
            return caster(value)
        except ValueError:
            continue
    return value


def _model_param_resolver(spec: Any) -> Optional[ModelDescriptor]:
    if not isinstance(spec, str) or not spec.startswith("model:"):
        return None
    _, remainder = spec.split("model:", 1)
    class_part, _, arg_part = remainder.partition(":")
    ProcessorRegistry.ensure_default_modules(DEFAULT_MODULES)
    try:
        model_cls = cast(
            type[FittingModel], ProcessorRegistry.get_processor(class_part)
        )
    except KeyError:
        module_name, sep, class_name = class_part.partition(".")
        if sep:
            module = importlib.import_module(module_name)
            model_cls = cast(type[FittingModel], getattr(module, class_name))
        else:
            raise
    if not issubclass(model_cls, FittingModel):
        raise ValueError(f"{class_part} is not a FittingModel subclass")
    kwargs: dict[str, Any] = {}
    if arg_part:
        for item in arg_part.split(","):
            if not item:
                continue
            key, _, val = item.partition("=")
            kwargs[key] = _parse_scalar(val)
    class_path = f"{model_cls.__module__}.{model_cls.__qualname__}"
    return ModelDescriptor(class_path, kwargs)


def register_builtin_resolvers() -> None:
    """Register all built-in name and parameter resolvers."""
    NameResolverRegistry.register_resolver("rename:", _resolve_rename)
    NameResolverRegistry.register_resolver("delete:", _resolve_delete)
    NameResolverRegistry.register_resolver("template:", _resolve_template)
    NameResolverRegistry.register_resolver("slice:", _resolve_slice)
    ParameterResolverRegistry.register_resolver(_model_param_resolver, builtin=True)


def reset_to_builtins() -> None:
    """Reset name resolvers to built-in defaults.

    This helper function clears all current name resolvers and re-registers
    only the built-in resolvers. This is useful in test environments where
    resolvers may have been modified and need to be restored to a known state.

    The built-in resolvers include:
    - rename: - Context key renaming
    - delete: - Context key deletion
    - template: - String template building
    - slice: - Data processor slicing

    Example:
        >>> from semantiva.registry.builtin_resolvers import reset_to_builtins
        >>> reset_to_builtins()  # Restore built-in resolvers after test cleanup
    """
    NameResolverRegistry.clear()
    register_builtin_resolvers()
