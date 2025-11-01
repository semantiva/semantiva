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

import pytest

from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.parametric_sweep_factory import (
    FromContext,
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
)
from semantiva.examples.test_utils import (
    FloatDataCollection,
    FloatDataType,
    FloatOperation,
)


class PairingOperation(FloatOperation):
    """Takes a pair=(x,y) and returns x+y as FloatDataType."""

    @classmethod
    def _process_logic(cls, data: FloatDataType, pair):
        x, y = pair
        return FloatDataType(float(data.data) + float(x) + int(y))


def test_tuple_argument_in_expression(float_data):
    Sweep = ParametricSweepFactory.create(
        element=PairingOperation,
        element_kind="DataOperation",
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 2.0, steps=3)},
        parametric_expressions={"pair": "(t*10.0, 20)"},
        mode="combinatorial",
        broadcast=False,
    )
    operation = Sweep()
    out = operation.process(float_data)
    assert [x.data for x in out] == [22.0, 32.0, 42.0]


def test_type_conversions_in_expression(empty_context):
    class EchoSource(DataSource):
        @classmethod
        def _get_data(cls, v: float, flag: bool):
            return FloatDataType(v if flag else -v)

        @classmethod
        def output_data_type(cls):
            return FloatDataType

    Sweep = ParametricSweepFactory.create(
        element=EchoSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": SequenceSpec(["1", "2", "0"])},
        parametric_expressions={
            "v": "float(t)",
            "flag": "bool(int(t))",
        },
        mode="by_position",
        broadcast=False,
    )
    out = Sweep._get_data(context=empty_context)
    assert [x.data for x in out] == [1.0, 2.0, -0.0]


def test_by_position_and_broadcast(empty_context):
    class SumSource(DataSource):
        @classmethod
        def _get_data(cls, a: float, b: float):
            return FloatDataType(a + b)

        @classmethod
        def output_data_type(cls):
            return FloatDataType

    with pytest.raises(ValueError):
        ParametricSweepFactory.create(
            element=SumSource,
            element_kind="DataSource",
            collection_output=FloatDataCollection,
            vars={"a": SequenceSpec([1.0, 2.0]), "b": SequenceSpec([10.0])},
            parametric_expressions={"a": "a", "b": "b"},
            mode="by_position",
            broadcast=False,
        )._get_data(context=empty_context)

    Sweep = ParametricSweepFactory.create(
        element=SumSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0]), "b": SequenceSpec([10.0])},
        parametric_expressions={"a": "a", "b": "b"},
        mode="by_position",
        broadcast=True,
    )
    out = Sweep._get_data(context=empty_context)
    assert [x.data for x in out] == [11.0, 12.0]


def test_from_context_sequence(empty_context):
    empty_context.set_value("vals", [3.0, 4.0, 5.0])

    class PassSource(DataSource):
        @classmethod
        def _get_data(cls, value: float):
            return FloatDataType(value)

        @classmethod
        def output_data_type(cls):
            return FloatDataType

    Sweep = ParametricSweepFactory.create(
        element=PassSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"v": FromContext("vals")},
        parametric_expressions={"value": "v"},
        mode="by_position",
        broadcast=False,
    )
    out = Sweep._get_data(context=empty_context, vals=empty_context.get_value("vals"))
    assert [x.data for x in out] == [3.0, 4.0, 5.0]
    assert empty_context.get_value("v_values") == [3.0, 4.0, 5.0]


def test_from_context_missing_key_raises(empty_context):
    class PassSource(DataSource):
        @classmethod
        def _get_data(cls, value: float):
            return FloatDataType(value)

        @classmethod
        def output_data_type(cls):
            return FloatDataType

    Sweep = ParametricSweepFactory.create(
        element=PassSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"v": FromContext("MISSING_KEY")},
        parametric_expressions={"value": "v"},
        mode="by_position",
        broadcast=False,
    )
    with pytest.raises(ValueError):
        Sweep._get_data(context=empty_context)
