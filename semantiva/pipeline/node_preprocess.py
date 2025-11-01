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

"""Helpers for preprocessing pipeline node configurations."""

from __future__ import annotations

from typing import Any, Dict, Literal

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
    FromContext,
)
from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.data_processors import DataOperation, DataProbe
from semantiva.data_types.data_types import DataCollectionType

from semantiva.registry.processor_registry import ProcessorRegistry


def _convert_var_specs(
    raw: dict[str, Any],
) -> dict[str, RangeSpec | SequenceSpec | FromContext]:
    processed: dict[str, RangeSpec | SequenceSpec | FromContext] = {}
    for var, spec in raw.items():
        if isinstance(spec, list):
            if len(spec) == 2 and all(isinstance(x, (int, float)) for x in spec):
                processed[var] = RangeSpec(
                    lo=float(spec[0]), hi=float(spec[1]), steps=10
                )
            else:
                processed[var] = SequenceSpec(spec)
            continue
        if not isinstance(spec, dict):
            raise ValueError(f"Variable '{var}' must be a list or dict specification")
        if "from_context" in spec:
            key = spec["from_context"]
            if not isinstance(key, str):
                raise ValueError(f"from_context value for '{var}' must be a string key")
            processed[var] = FromContext(key)
            continue
        if {"lo", "hi", "steps"}.issubset(spec):
            processed[var] = RangeSpec(
                lo=float(spec["lo"]),
                hi=float(spec["hi"]),
                steps=int(spec["steps"]),
                scale=spec.get("scale", "linear"),
                endpoint=spec.get("endpoint", True),
            )
            continue
        if "values" in spec:
            processed[var] = SequenceSpec(spec["values"])
            continue
        raise ValueError(f"Invalid var specification for '{var}': {spec}")
    return processed


def preprocess_node_config(node_config: Dict[str, Any]) -> Dict[str, Any]:
    """Handle structured sweep definitions prior to symbol resolution."""

    processor_spec = node_config.get("processor")

    if not (isinstance(processor_spec, str) and processor_spec.startswith("sweep:")):
        return node_config

    declarative = node_config.get("declarative")
    if not isinstance(declarative, dict):
        raise ValueError("Sweep declarative block must be provided as a mapping")

    vars_spec = declarative.get("vars")
    if not isinstance(vars_spec, dict) or not vars_spec:
        raise ValueError("declarative.vars must be a non-empty mapping")

    processed_vars = _convert_var_specs(vars_spec)

    expr_spec = declarative.get("expr", {}) or {}
    if not isinstance(expr_spec, dict):
        raise ValueError("declarative.expr must be a mapping of parameter expressions")

    mode = declarative.get("mode", "combinatorial")
    broadcast = declarative.get("broadcast", False)
    if not isinstance(broadcast, bool):
        raise ValueError("declarative.broadcast must be a boolean value")

    parts = processor_spec.split(":")
    if len(parts) not in (2, 3):
        raise ValueError(
            "Invalid sweep processor; expected 'sweep:<Element>' or 'sweep:<Element>:<Collection>'"
        )

    _, element_name, *rest = parts
    collection_name = rest[0] if rest else None

    element_cls = ProcessorRegistry.get_processor(element_name)
    if not isinstance(element_cls, type):
        raise TypeError(f"Processor '{element_name}' did not resolve to a class")

    element_kind: Literal["DataSource", "DataOperation", "DataProbe"]
    if issubclass(element_cls, DataSource):
        element_kind = "DataSource"
    elif issubclass(element_cls, DataOperation):
        element_kind = "DataOperation"
    elif issubclass(element_cls, DataProbe):
        element_kind = "DataProbe"
    else:
        raise ValueError(
            f"{element_name} must resolve to a DataSource, DataOperation, or DataProbe subclass"
        )

    collection_cls = None
    if element_kind == "DataProbe":
        if collection_name is not None:
            raise ValueError(
                "DataProbe sweeps must not declare a collection output in the processor string"
            )
    else:
        if collection_name is None:
            raise ValueError(
                "DataSource/DataOperation sweeps require an output collection in the processor string"
            )
        candidate = ProcessorRegistry.get_processor(collection_name)
        if not (
            isinstance(candidate, type) and issubclass(candidate, DataCollectionType)
        ):
            raise ValueError(
                f"{collection_name} must resolve to a DataCollectionType subclass for sweep output"
            )
        collection_cls = candidate

    sweep_class = ParametricSweepFactory.create(
        element=element_cls,
        element_kind=element_kind,
        collection_output=collection_cls,
        vars=processed_vars,
        parametric_expressions=expr_spec,
        mode=mode,
        broadcast=broadcast,
    )

    new_config = dict(node_config)
    new_config["processor"] = sweep_class
    new_config.pop("declarative", None)
    return new_config
