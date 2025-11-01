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

"""Factory-level validation for parametric sweep v2."""

from __future__ import annotations

import inspect

import pytest

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
    FromContext,
    VarSpec,
)
from semantiva.examples.test_utils import (
    FloatValueDataSourceWithDefault,
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatDataCollection,
)
from semantiva.inspection.builder import build_pipeline_inspection
from semantiva.registry import ProcessorRegistry


def test_factory_rejects_unknown_expression_keys() -> None:
    """Expressions must only target parameters accepted by the element."""

    vars_spec: dict[str, VarSpec] = {"t": RangeSpec(lo=0.0, hi=1.0, steps=2)}

    with pytest.raises(TypeError, match="unknown parameters"):
        ParametricSweepFactory.create(
            element=FloatValueDataSourceWithDefault,
            element_kind="DataSource",
            collection_output=FloatDataCollection,
            vars=vars_spec,
            parametric_expressions={"not_a_param": "t"},
        )


def test_data_operation_missing_arg_exposed_on_signature() -> None:
    """Required call arguments without expressions surface on the sweep interface."""

    sweep_cls = ParametricSweepFactory.create(
        element=FloatMultiplyOperation,
        element_kind="DataOperation",
        collection_output=FloatDataCollection,
        vars={"factor_seed": SequenceSpec([1.0, 2.0])},
        parametric_expressions={},
    )

    params = sweep_cls.get_processing_parameter_names()
    assert params == ["factor"]
    required = sweep_cls.get_required_external_parameters()
    assert required == ["factor"]

    signature = inspect.signature(sweep_cls._process_logic)
    assert "factor" in signature.parameters
    assert signature.parameters["factor"].default is inspect._empty


def test_data_source_from_context_requirement_is_exposed() -> None:
    """FromContext variables become explicit processor requirements."""

    sweep_cls = ParametricSweepFactory.create(
        element=FloatValueDataSourceWithDefault,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": FromContext("t_values")},
        parametric_expressions={"value": "t"},
    )

    assert sweep_cls.get_processing_parameter_names() == [
        "t_values"
    ], "data source sweep should expose context keys"
    assert sweep_cls.get_required_external_parameters() == ["t_values"]

    signature = inspect.signature(sweep_cls._get_data)
    assert "t_values" in signature.parameters


def test_data_probe_required_external_parameters_include_context() -> None:
    """DataProbe sweeps expose FromContext variables even without expressions."""

    sweep_cls = ParametricSweepFactory.create(
        element=FloatCollectValueProbe,
        element_kind="DataProbe",
        collection_output=None,
        vars={"seed": FromContext("probe_sequence")},
        parametric_expressions={},
    )

    assert sweep_cls.get_processing_parameter_names() == ["probe_sequence"]
    assert sweep_cls.get_required_external_parameters() == ["probe_sequence"]

    signature = inspect.signature(sweep_cls._process_logic)
    assert "probe_sequence" in signature.parameters


def test_inspection_reports_required_external_parameters() -> None:
    """Inspection surfaces unbound parameters from the sweep processor."""

    ProcessorRegistry.clear()
    ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])
    try:
        node_configs = [
            {
                "processor": "FloatValueDataSource",
                "parameters": {"value": 2.0},
            },
            {
                "processor": "FloatMultiplyOperation",
                "derive": {
                    "parameter_sweep": {
                        "parameters": {},
                        "variables": {"placeholder": {"values": [0]}},
                        "collection": "FloatDataCollection",
                    }
                },
                "parameters": {},
            },
        ]

        inspection = build_pipeline_inspection(node_configs)
        required = inspection.nodes[1].required_external_parameters
        assert required == ["factor"]
    finally:
        ProcessorRegistry.clear()
