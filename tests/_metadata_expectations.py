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

"""Helper utilities for metadata contract validation.

The `EXPECTATIONS` mapping below acts as the single source of truth for
component metadata requirements. When a new component category is
introduced, extend this mapping with a :class:`ComponentExpectation`
entry and provide concrete components that satisfy the declared
contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Set, Type

from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.data_types import NoDataType

Validator = Callable[[Type[_SemantivaComponent], dict], None]


@dataclass
class ComponentExpectation:
    """Expected metadata contract for a component category."""

    required: Set[str]
    forbidden: Set[str]
    validators: Dict[str, Validator] = field(default_factory=dict)


def _validate_parameters(_cls: Type[_SemantivaComponent], metadata: dict) -> None:
    params = metadata["parameters"]
    if params not in ("None", {}, None):
        assert isinstance(
            params, (dict, list)
        ), "parameters must be dict, list, 'None', or {}"


def _validate_injected_context(_cls: Type[_SemantivaComponent], metadata: dict) -> None:
    if "injected_context_keys" in metadata:
        assert isinstance(metadata["injected_context_keys"], list)


def _validate_source_node(cls: Type[_SemantivaComponent], metadata: dict) -> None:
    assert metadata.get("input_data_type") == NoDataType.__name__
    if hasattr(cls, "processor"):
        expected = cls.processor.output_data_type().__name__
        assert metadata.get("output_data_type") == expected


def _validate_sink_node(cls: Type[_SemantivaComponent], metadata: dict) -> None:
    if hasattr(cls, "processor"):
        expected = cls.processor.input_data_type().__name__
        assert metadata.get("input_data_type") == expected
        assert metadata.get("output_data_type") == expected


def _validate_operation_node(cls: Type[_SemantivaComponent], metadata: dict) -> None:
    if hasattr(cls, "processor"):
        assert (
            metadata.get("input_data_type") == cls.processor.input_data_type().__name__
        )
        assert (
            metadata.get("output_data_type")
            == cls.processor.output_data_type().__name__
        )


def _validate_probe_node(cls: Type[_SemantivaComponent], metadata: dict) -> None:
    if hasattr(cls, "processor"):
        expected = cls.processor.input_data_type().__name__
        assert metadata.get("input_data_type") == expected
        assert metadata.get("output_data_type") == expected


EXPECTATIONS: Dict[str, ComponentExpectation] = {
    "DataSource": ComponentExpectation(
        required={"output_data_type"},
        forbidden={"input_data_type"},
        validators={"parameters": _validate_parameters},
    ),
    "PayloadSource": ComponentExpectation(
        required={"output_data_type"},
        forbidden={"input_data_type"},
        validators={
            "parameters": _validate_parameters,
            "injected_context_keys": _validate_injected_context,
        },
    ),
    "DataSink": ComponentExpectation(
        required={"input_data_type"},
        forbidden={"output_data_type"},
        validators={"parameters": _validate_parameters},
    ),
    "PayloadSink": ComponentExpectation(
        required={"input_data_type"},
        forbidden={"output_data_type"},
        validators={"parameters": _validate_parameters},
    ),
    "DataOperation": ComponentExpectation(
        required={"input_data_type", "output_data_type", "parameters"},
        forbidden=set(),
        validators={"parameters": _validate_parameters},
    ),
    "DataProbe": ComponentExpectation(
        required={"input_data_type"},
        forbidden={"output_data_type"},
        validators={"parameters": _validate_parameters},
    ),
    "ContextProcessor": ComponentExpectation(
        required=set(),
        forbidden={"input_data_type", "output_data_type"},
        validators={},
    ),
    "DataSourceNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_source_node},
    ),
    "PayloadSourceNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_source_node},
    ),
    "DataSinkNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_sink_node},
    ),
    "PayloadSinkNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_sink_node},
    ),
    "DataOperationNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_operation_node},
    ),
    "ProbeContextInjectorNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_probe_node},
    ),
    "ProbeResultCollectorNode": ComponentExpectation(
        required={"input_data_type", "output_data_type"},
        forbidden=set(),
        validators={"delegation": _validate_probe_node},
    ),
}


def get_component_category(cls: Type[_SemantivaComponent], metadata: dict) -> str:
    """Derive the expectation category for ``cls``."""
    return metadata.get("component_type", cls.__name__)


def validate_component_metadata(cls: Type[_SemantivaComponent]) -> None:
    base_metadata = cls._define_metadata()
    assert isinstance(base_metadata, dict)
    metadata = cls.get_metadata()
    assert isinstance(metadata, dict)
    for key in ("class_name", "docstring", "component_type"):
        assert key in metadata, f"{cls.__name__}: missing base key {key}"
    if "parameters" in metadata:
        _validate_parameters(cls, metadata)
    _validate_injected_context(cls, metadata)

    from semantiva.core.semantiva_component import get_component_registry

    registry = get_component_registry()
    for comp_type, classes in registry.items():
        if cls in classes:
            assert (
                metadata.get("component_type") == comp_type
            ), f"{cls.__name__}: component_type mismatch"
    category = get_component_category(cls, metadata)
    expectation = EXPECTATIONS.get(category)
    if expectation:
        missing = expectation.required - metadata.keys()
        assert not missing, f"{cls.__name__}: missing required keys {missing}"
        forbidden = expectation.forbidden & metadata.keys()
        assert not forbidden, f"{cls.__name__}: forbidden keys present {forbidden}"
        for fn in expectation.validators.values():
            fn(cls, metadata)
    if (
        metadata.get("component_type", "").endswith("Sink")
        and "input_data_type" in metadata
        and "output_data_type" in metadata
    ):
        assert (
            metadata["input_data_type"] == metadata["output_data_type"]
        ), f"{cls.__name__}: sink input/output mismatch"
