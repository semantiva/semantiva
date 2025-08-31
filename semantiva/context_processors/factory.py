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
Dynamic context processors for common transformations.

This module provides factory functions that generate ContextProcessor subclasses
at runtime for simple context manipulations such as renaming and deletion.

Factories:

- create_rename_operation(original_key, destination_key)
- create_delete_operation(key)

Each factory returns a class with:

- a properly introspectable `_process_logic(...)` signature (no `exec`)
- `get_created_keys()` / `get_suppressed_keys()` consistent with behavior
- a descriptive `__doc__` for generated classes

These classes participate fully in parameter resolution and validation.
"""

from typing import List
from semantiva.context_processors.context_processors import (
    ContextProcessor,
)


def _context_renamer_factory(
    original_key: str, destination_key: str
) -> type[ContextProcessor]:
    """Create a ContextProcessor subclass that renames a context key."""

    param_name = original_key.replace(".", "_")

    def create_process_logic_with_signature():
        import inspect

        def _process_logic_with_signature(self, **kwargs):
            """Rename the resolved '{original_key}' value to '{destination_key}'."""
            value = kwargs.get(param_name)
            if value is not None:
                self._notify_context_update(destination_key, value)
                self._notify_context_deletion(original_key)
                self.logger.debug(
                    f"Renamed context key '{original_key}' -> '{destination_key}'"
                )
            else:
                self.logger.warning(
                    f"Key '{original_key}' not found in resolved parameters."
                )

        old_sig = inspect.signature(_process_logic_with_signature)
        new_params = [
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ]
        for param in old_sig.parameters.values():
            if param.name not in ["self"]:
                new_params.append(param)

        new_sig = inspect.Signature(new_params)
        _process_logic_with_signature.__signature__ = new_sig
        _process_logic_with_signature.__name__ = "_process_logic_with_signature"
        return _process_logic_with_signature

    _process_logic = create_process_logic_with_signature()

    def get_created_keys(cls) -> List[str]:
        return [destination_key]

    def get_suppressed_keys(cls) -> List[str]:
        return [original_key]

    def context_keys(cls) -> List[str]:
        return [destination_key]

    def get_processing_parameter_names(cls) -> List[str]:
        return [original_key]

    dynamic_class_name = f"Rename_{original_key}_to_{destination_key}"
    class_attrs = {
        "_process_logic": _process_logic,
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
        "get_processing_parameter_names": classmethod(get_processing_parameter_names),
    }
    class_attrs["__doc__"] = (
        f"Renames context key '{original_key}' to '{destination_key}'. "
        "Reads the original value from resolved parameters and writes the new key, "
        "then suppresses the original key."
    )
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)


def _context_deleter_factory(key: str) -> type[ContextProcessor]:
    """Create a ContextProcessor subclass that deletes a context key."""

    def create_process_logic_with_signature():
        import inspect

        def _process_logic_with_signature(self):
            """Delete key '{key}' from context via the observer."""
            self._notify_context_deletion(key)
            self.logger.debug(f"Deleted context key '{key}'")

        sig = inspect.Signature(
            [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        )
        _process_logic_with_signature.__signature__ = sig
        _process_logic_with_signature.__name__ = "_process_logic_with_signature"
        return _process_logic_with_signature

    _process_logic = create_process_logic_with_signature()

    def get_created_keys(cls) -> List[str]:
        return []

    def get_suppressed_keys(cls) -> List[str]:
        return [key]

    def context_keys(cls) -> List[str]:
        return []

    def get_processing_parameter_names(cls) -> List[str]:
        return []

    class_attrs = {
        "_process_logic": _process_logic,
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
        "get_processing_parameter_names": classmethod(get_processing_parameter_names),
    }
    dynamic_class_name = f"Delete_{key}"
    class_attrs["__doc__"] = (
        f"Deletes context key '{key}'. If the key is present after parameter "
        "resolution, it is removed via the observer."
    )
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)


def create_rename_operation(
    original_key: str, destination_key: str
) -> type[ContextProcessor]:
    """Public factory for renaming context keys."""
    return _context_renamer_factory(original_key, destination_key)


def create_delete_operation(key: str) -> type[ContextProcessor]:
    """Public factory for deleting a context key."""
    return _context_deleter_factory(key)
