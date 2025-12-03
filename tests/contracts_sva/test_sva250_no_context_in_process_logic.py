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

"""Unit tests for SVA250 (_process_logic must not accept ContextType).

These tests exercise the contract validator directly to ensure that
``semantiva dev lint`` can emit SVA250 diagnostics consistent with the
documentation and contracts catalog.

This module lives under tests/contracts_sva/ so that all SVA rule
validations are co-located and easy to expand.
"""

from __future__ import annotations

from typing import Any, Dict, List

from semantiva.contracts.expectations import validate_components
from semantiva.context_processors.context_types import ContextType


class _BadOperationWithContextParam:
    """Intentionally bad DataOperation-style component using `context` param name."""

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:  # pragma: no cover - simple metadata
        return {
            "class_name": cls.__name__,
            "docstring": "Bad test operation using context parameter.",
            "component_type": "DataOperation",
            # Provide minimal IO metadata to satisfy DataOperation rules
            "input_data_type": "BaseDataType",
            "output_data_type": "BaseDataType",
        }

    def _process_logic(self, data: Any, context: Any) -> Any:  # type: ignore[unused-argument]
        # The body is irrelevant; the signature is what SVA250 inspects.
        return data


class _BadOperationWithContextAnnotation:
    """Intentionally bad DataOperation using ContextType annotation only."""

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:  # pragma: no cover - simple metadata
        return {
            "class_name": cls.__name__,
            "docstring": "Bad test operation using ContextType annotation.",
            "component_type": "DataOperation",
            "input_data_type": "BaseDataType",
            "output_data_type": "BaseDataType",
        }

    def _process_logic(self, data: Any, ctx: ContextType) -> Any:  # type: ignore[unused-argument]
        # The body is irrelevant; the annotation is what SVA250 inspects.
        return data


class _GoodOperationNoContext:
    """Well-formed DataOperation-style component without context parameters."""

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:  # pragma: no cover - simple metadata
        return {
            "class_name": cls.__name__,
            "docstring": "Good test operation without context parameters.",
            "component_type": "DataOperation",
            "input_data_type": "BaseDataType",
            "output_data_type": "BaseDataType",
        }

    def _process_logic(self, data: Any, factor: float = 1.0) -> Any:  # type: ignore[unused-argument]
        return data


def _codes(diags) -> List[str]:
    return [d.code for d in diags]


def test_sva250_flags_context_parameter_name() -> None:
    """SVA250 should trigger when _process_logic has a `context` parameter name."""

    diags = validate_components([_BadOperationWithContextParam])
    codes = set(_codes(diags))

    assert "SVA250" in codes


def test_sva250_flags_contexttype_annotation() -> None:
    """SVA250 should trigger when _process_logic is annotated with ContextType."""

    diags = validate_components([_BadOperationWithContextAnnotation])
    codes = set(_codes(diags))

    assert "SVA250" in codes


def test_sva250_not_emitted_for_valid_operation() -> None:
    """Well-formed operations without context parameters should not emit SVA250."""

    diags = validate_components([_GoodOperationNoContext])
    codes = set(_codes(diags))

    assert "SVA250" not in codes
