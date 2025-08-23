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


"""Lightweight class descriptors for deferred instantiation.

Semantiva pipelines often refer to components (models, processors, helpers) by
import path and parameters instead of constructing them eagerly. This module
defines a small descriptor format and helpers to:

    - Represent a component as ``{"class": "pkg.mod.Class", "kwargs": {...}}``
        or via the :class:`ModelDescriptor` dataclass.
    - Convert nested structures that may contain descriptors to plain JSON
        (``descriptor_to_json``).
    - Instantiate descriptor-bearing structures into concrete objects
        (``instantiate_from_descriptor``).

Contracts and behavior
    - ``class`` must be an importable dotted path. Import errors will propagate.
    - ``kwargs`` is recursively processed so nested descriptors are supported.
    - Non-descriptor dicts/lists are traversed and returned with values
        instantiated when applicable.

This facility is used by the orchestrator when resolving node parameters.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from importlib import import_module


def _import_from_path(class_path: str):
    """Import and return a class or callable from a dotted path.

    Args:
        class_path: Dotted import path (e.g., ``"package.module.Class"``).

    Returns:
        The imported attribute referenced by the final segment of the path.

    Raises:
        ImportError, AttributeError: If the module or attribute cannot be resolved.
    """
    module_name, _, cls_name = class_path.rpartition(".")
    module = import_module(module_name)
    return getattr(module, cls_name)


@dataclass
class ModelDescriptor:
    """Descriptor for a constructible object.

    Attributes:
        class_path: Dotted path to the target class or callable.
        kwargs: Keyword arguments used to instantiate the target.

    Notes:
        Use :meth:`to_json` to turn nested descriptors into a JSON-friendly dict.
        Use :meth:`instantiate` to construct the target recursively.
    """

    class_path: str
    kwargs: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping for this descriptor.

        Returns a dict with keys ``class`` and ``kwargs``, converting any nested
        descriptors within ``kwargs`` via :func:`descriptor_to_json`.
        """
        return {"class": self.class_path, "kwargs": descriptor_to_json(self.kwargs)}

    def instantiate(self) -> Any:
        """Instantiate the described class, resolving nested descriptors.

        Returns:
            The constructed object ``cls(**kwargs)`` after recursively applying
            :func:`instantiate_from_descriptor` to ``kwargs``.
        """
        cls = _import_from_path(self.class_path)
        kwargs = instantiate_from_descriptor(self.kwargs)
        return cls(**kwargs)


def descriptor_to_json(obj: Any) -> Any:
    """Recursively convert descriptors to JSON-compatible structures.

    - :class:`ModelDescriptor` → ``{"class": ..., "kwargs": ...}``
    - dict/list containers are traversed; values are converted when needed.
    - Other objects are returned unchanged.
    """
    if isinstance(obj, ModelDescriptor):
        return obj.to_json()
    if isinstance(obj, dict):
        return {k: descriptor_to_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [descriptor_to_json(v) for v in obj]
    return obj


def instantiate_from_descriptor(obj: Any) -> Any:
    """Recursively instantiate any descriptors contained in ``obj``.

    Supported forms:
      - :class:`ModelDescriptor`
      - Mapping with exactly the keys ``{"class", "kwargs"}``
      - Lists/dicts containing the above

    Returns ``obj`` unchanged if no descriptors are present.
    """
    if isinstance(obj, ModelDescriptor):
        return obj.instantiate()
    if isinstance(obj, dict):
        if set(obj.keys()) == {"class", "kwargs"}:
            cls = _import_from_path(obj["class"])
            kwargs = instantiate_from_descriptor(obj.get("kwargs", {}))
            return cls(**kwargs)
        return {k: instantiate_from_descriptor(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [instantiate_from_descriptor(v) for v in obj]
    return obj
