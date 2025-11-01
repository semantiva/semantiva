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

"""Preprocess node configurations.

Currently recognized tool under the reserved node key ``derive``:

- ``parameter_sweep``: generates a specialized processor class that computes
  **parameters** from **variables** (using expressions) and produces collection
  outputs or lists of probe results from swept parameter values.

Rules:
- DataSource/DataOperation require ``collection`` (typed collection class name).
- DataProbe forbids ``collection`` and returns a list of probe results; the probe
  node persists via ``context_key`` (node-level) and passes input through.
- Unknown parameter names in ``parameters`` (inside parameter_sweep) raise a ValueError.
- Node ``parameters`` are not modified; they are merged at runtime:
  computed > provided > defaults.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, cast

from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.data_processors import DataOperation, DataProbe
from semantiva.data_processors.parametric_sweep_factory import (
    FromContext,
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
)
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

    derive = node_config.get("derive")
    if not (
        isinstance(derive, dict) and isinstance(derive.get("parameter_sweep"), dict)
    ):
        return node_config

    sweep_cfg = derive["parameter_sweep"]

    params_spec = sweep_cfg.get("parameters", {})
    if not isinstance(params_spec, dict):
        raise ValueError("derive.parameter_sweep.parameters must be a mapping")

    vars_spec = sweep_cfg.get("variables")
    if not isinstance(vars_spec, dict) or not vars_spec:
        raise ValueError("derive.parameter_sweep.variables must be a non-empty mapping")

    mode = sweep_cfg.get("mode", "combinatorial")
    if not isinstance(mode, str):
        raise ValueError("derive.parameter_sweep.mode must be a string")
    if mode not in {"combinatorial", "by_position"}:
        raise ValueError(
            "derive.parameter_sweep.mode must be 'combinatorial' or 'by_position'"
        )

    broadcast = sweep_cfg.get("broadcast", False)
    if not isinstance(broadcast, bool):
        raise ValueError("derive.parameter_sweep.broadcast must be a boolean value")

    processed_vars = _convert_var_specs(vars_spec)

    processor_spec = node_config.get("processor")
    if processor_spec is None:
        raise ValueError("derive.parameter_sweep requires a processor specification")

    element_cls: type[Any]
    element_name: str
    if isinstance(processor_spec, str):
        element_name = processor_spec
        element_cls = ProcessorRegistry.get_processor(processor_spec)
    elif isinstance(processor_spec, type):
        element_cls = processor_spec
        element_name = element_cls.__name__
    else:
        raise TypeError(
            "processor must be a string or class when using derive.parameter_sweep"
        )

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
    collection_name = sweep_cfg.get("collection")
    if element_kind == "DataProbe":
        if collection_name is not None:
            raise ValueError("DataProbe sweeps must not declare a collection")
    else:
        if not isinstance(collection_name, str) or not collection_name:
            raise ValueError(
                "DataSource/DataOperation sweeps require derive.parameter_sweep.collection"
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
        parametric_expressions=params_spec,
        mode=cast(Literal["combinatorial", "by_position"], mode),
        broadcast=broadcast,
    )

    new_config = dict(node_config)
    new_config["processor"] = sweep_class

    remaining_derive = dict(derive)
    remaining_derive.pop("parameter_sweep", None)
    if remaining_derive:
        new_config["derive"] = remaining_derive
    else:
        new_config.pop("derive", None)

    return new_config
