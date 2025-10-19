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

from typing import Any, Dict

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
    FromContext,
)
from semantiva.data_io.data_io import DataSource
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
    parameters = node_config.get("parameters", {})

    if not (isinstance(processor_spec, str) and processor_spec.startswith("sweep:")):
        return node_config

    if not isinstance(parameters, dict):
        raise ValueError("Sweep parameters must be provided as a mapping")

    parts = processor_spec.split(":")
    if len(parts) != 3:
        raise ValueError(
            "Invalid sweep processor; expected 'sweep:DataSource:Collection'"
        )

    _, source_name, collection_name = parts

    if "vars" not in parameters:
        raise ValueError("vars must be a non-empty dictionary")

    vars_spec = parameters.get("vars", {})
    if not isinstance(vars_spec, dict) or not vars_spec:
        raise ValueError("vars must be a non-empty dictionary")

    processed_vars = _convert_var_specs(vars_spec)

    parametric_expressions = parameters.get("parametric_expressions") or None
    static_params = parameters.get("static_params") or None
    mode = parameters.get("mode", "combinatorial")
    broadcast = parameters.get("broadcast", False)
    include_independent = parameters.get("include_independent", False)

    source_cls = ProcessorRegistry.get_processor(source_name)
    collection_cls = ProcessorRegistry.get_processor(collection_name)

    if not issubclass(source_cls, DataSource):
        raise ValueError(f"{source_name} is not a DataSource subclass")
    if not issubclass(collection_cls, DataCollectionType):
        raise ValueError(f"{collection_name} is not a DataCollectionType subclass")

    sweep_class = ParametricSweepFactory.create(
        element=source_cls,
        element_kind="DataSource",
        collection_output=collection_cls,
        vars=processed_vars,
        parametric_expressions=parametric_expressions,
        static_params=static_params,
        mode=mode,
        broadcast=broadcast,
        include_independent=include_independent,
    )

    new_config = dict(node_config)
    new_config["processor"] = sweep_class
    new_config["parameters"] = {}
    return new_config
