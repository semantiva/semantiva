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

"""Dynamic context processors for common transformations."""

import re
from string import Formatter
from typing import List


from semantiva.context_processors.context_processors import (
    ContextProcessor,
)


_SAFE_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_PLACEHOLDER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ensure_valid_key(key: str) -> None:
    if not _SAFE_KEY_PATTERN.fullmatch(key):
        message = (
            "Context keys must match ^[A-Za-z_][A-Za-z0-9_.]*$; " f"received {key!r}"
        )
        raise ValueError(message)


def _sanitize_identifier(key: str) -> str:
    identifier = key.replace(".", "_")
    if not identifier or not identifier[0].isalpha() and identifier[0] != "_":
        raise ValueError(f"Unable to derive a safe identifier from context key {key!r}")
    return identifier


def _extract_strict_placeholders(template: str) -> List[str]:
    """Return placeholder names from a template enforcing strict identifier rules."""

    formatter = Formatter()
    required: List[str] = []
    seen: set[str] = set()
    for literal, field_name, format_spec, conversion in formatter.parse(template):
        if field_name is None:
            continue
        if field_name == "":
            raise ValueError("Positional placeholders '{}' are not supported")
        if conversion is not None:
            raise ValueError(
                "Format conversions (e.g., '!r') are not supported in template resolvers"
            )
        if format_spec:
            raise ValueError(
                "Format specifications (e.g., ':03d') are not supported in template resolvers"
            )
        if not _PLACEHOLDER_PATTERN.fullmatch(field_name):
            raise ValueError(
                "Placeholder names must match [A-Za-z_][A-Za-z0-9_]*; "
                f"received {field_name!r}"
            )
        if field_name not in seen:
            seen.add(field_name)
            required.append(field_name)

    if not required:
        raise ValueError(
            "Template resolvers must include at least one placeholder like '{key}'"
        )
    return required


def _context_renamer_factory(
    original_key: str, destination_key: str
) -> type[ContextProcessor]:
    """Create a ContextProcessor subclass that renames a context key."""

    _ensure_valid_key(original_key)
    _ensure_valid_key(destination_key)

    # We'll keep the runtime function simple and map kwargs -> arg in operate_context
    class_suffix_src = _sanitize_identifier(original_key)
    class_suffix_dst = _sanitize_identifier(destination_key)

    def _process_logic(self, **kwargs):
        """Rename the resolved 'original_key' value to 'destination_key'."""
        value = kwargs.get(original_key)
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

    def get_created_keys(cls) -> List[str]:
        return [destination_key]

    def get_suppressed_keys(cls) -> List[str]:
        return [original_key]

    def context_keys(cls) -> List[str]:
        return [destination_key]

    def get_processing_parameter_names(cls) -> List[str]:
        return [original_key]

    dynamic_class_name = f"Rename_{class_suffix_src}_to_{class_suffix_dst}"
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

    _ensure_valid_key(key)

    param_name = _sanitize_identifier(key)

    def _process_logic(self, **kwargs):
        """Delete key 'key' from context via the observer."""
        # The key should be available in resolved parameters if it exists
        value = kwargs.get(key)
        if value is not None:
            self._notify_context_deletion(key)
            self.logger.debug(f"Deleted context key '{key}'")
        else:
            self.logger.warning(f"Key '{key}' not found, nothing to delete")

    def get_created_keys(cls) -> List[str]:
        return []

    def get_suppressed_keys(cls) -> List[str]:
        return [key]

    def context_keys(cls) -> List[str]:
        return []

    def get_processing_parameter_names(cls) -> List[str]:
        return [key]

    class_attrs = {
        "_process_logic": _process_logic,
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
        "get_processing_parameter_names": classmethod(get_processing_parameter_names),
    }
    dynamic_class_name = f"Delete_{param_name}"
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


def _context_template_factory(template: str, output_key: str) -> type[ContextProcessor]:
    """Create a ContextProcessor subclass that renders templates from context keys."""

    _ensure_valid_key(output_key)
    required_keys = _extract_strict_placeholders(template)
    class_suffix_out = _sanitize_identifier(output_key)

    def _process_logic(self, **kwargs):
        missing = [key for key in required_keys if key not in kwargs]
        if missing:
            raise KeyError(
                "Context template missing required keys: " + ", ".join(sorted(missing))
            )

        values = {name: str(kwargs[name]) for name in required_keys}
        rendered = template.format(**values)
        self._notify_context_update(output_key, rendered)
        self.logger.debug(
            "Template wrote %s=%r using keys %s",
            output_key,
            rendered,
            required_keys,
        )

    def get_created_keys(cls) -> List[str]:
        return [output_key]

    def get_suppressed_keys(cls) -> List[str]:
        return []

    def context_keys(cls) -> List[str]:
        return [output_key]

    def get_processing_parameter_names(cls) -> List[str]:
        return list(required_keys)

    dynamic_class_name = f"Template_{class_suffix_out}"
    class_attrs = {
        "_process_logic": _process_logic,
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
        "get_processing_parameter_names": classmethod(get_processing_parameter_names),
        "__doc__": (
            f"Builds a string from template {template!r} and writes it to "
            f"context key '{output_key}'."
        ),
    }
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)


def create_template_operation(template: str, output_key: str) -> type[ContextProcessor]:
    """Public factory for template-driven context processors."""

    return _context_template_factory(template, output_key)
