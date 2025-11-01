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

import inspect

import pytest

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
)
from semantiva.data_io.data_io import DataSource
from semantiva.examples.test_utils import (
    FloatCollectValueProbe,
    FloatDataCollection,
    FloatDataType,
    FloatMultiplyOperation,
    FloatValueDataSource,
)


def test_factory_datasource_happy_path_and_context(empty_context):
    Sweep = ParametricSweepFactory.create(
        element=FloatValueDataSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(-1.0, 2.0, steps=3)},
        parametric_expressions={"value": "2.0 * t"},
        mode="combinatorial",
        broadcast=False,
    )
    out = Sweep._get_data(context=empty_context)
    assert [x.data for x in out] == [-2.0, 1.0, 4.0]
    tvals = empty_context.get_value("t_values")
    assert len(tvals) == 3


def test_factory_operation_builds_collection(float_data):
    assert isinstance(float_data, FloatDataType)
    Sweep = ParametricSweepFactory.create(
        element=FloatMultiplyOperation,
        element_kind="DataOperation",
        collection_output=FloatDataCollection,
        vars={"f": RangeSpec(1.0, 3.0, steps=3)},
        parametric_expressions={"factor": "f"},
        mode="by_position",
        broadcast=False,
    )
    operation = Sweep()
    out = operation.process(float_data)
    assert isinstance(out, FloatDataCollection)
    assert [x.data for x in out] == [2.0, 4.0, 6.0]


def test_factory_probe_returns_list_and_preserves_input():
    Sweep = ParametricSweepFactory.create(
        element=FloatCollectValueProbe,
        element_kind="DataProbe",
        collection_output=None,
        vars={"n": RangeSpec(1, 3, steps=3)},
        parametric_expressions={},
        mode="combinatorial",
        broadcast=False,
    )
    data = FloatDataType(10.0)
    probe = Sweep()
    results = probe.process(data)
    assert results == [10.0, 10.0, 10.0]


class ValidSource(DataSource):
    @classmethod
    def output_data_type(cls):
        return FloatDataType

    @classmethod
    def _get_data(cls, a: float, b: int):
        return FloatDataType(a + b)


def test_unknown_expr_key_is_error():
    with pytest.raises(TypeError):
        ParametricSweepFactory.create(
            element=ValidSource,
            element_kind="DataSource",
            collection_output=FloatDataCollection,
            vars={"t": RangeSpec(0.0, 1.0, steps=2)},
            parametric_expressions={"bad": "t"},
            mode="combinatorial",
            broadcast=False,
        )


def test_missing_required_param_is_exposed_not_error():
    Sweep = ParametricSweepFactory.create(
        element=ValidSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=2)},
        parametric_expressions={"a": "t"},
        mode="combinatorial",
        broadcast=False,
    )
    sig = inspect.signature(Sweep._get_data)
    assert "b" in sig.parameters


def test_expression_overrides_pipeline_kwargs(empty_context):
    Sweep = ParametricSweepFactory.create(
        element=FloatValueDataSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(1.0, 1.0, steps=1)},
        parametric_expressions={"value": "2.0 * t"},
        mode="combinatorial",
        broadcast=False,
    )
    out = Sweep._get_data(context=empty_context, value=999.0)
    assert [x.data for x in out] == [2.0]
