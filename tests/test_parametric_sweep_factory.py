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

"""Tests for ParametricSweepFactory with DataSource outputs."""

from typing import Any, cast
import numpy as np
import pytest

from semantiva.context_processors.context_types import ContextType
from semantiva.data_io import DataSource
from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
    SequenceSpec,
    FromContext,
)
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import FloatDataCollection, FloatDataType
from semantiva.pipeline import Payload, Pipeline


class ParamSource(DataSource):
    """Simple DataSource that returns FloatDataType for a given value."""

    @classmethod
    def _get_data(cls, value: float) -> FloatDataType:
        return FloatDataType(value)

    @classmethod
    def output_data_type(cls):
        return FloatDataType


@pytest.fixture
def basic_sweep_config() -> dict[str, Any]:
    return {
        "element": ParamSource,
        "collection_output": FloatDataCollection,
        "vars": {"t": RangeSpec(0.0, 1.0, steps=4)},
        "parametric_expressions": {"value": "t"},
    }


def test_factory_creates_processor(basic_sweep_config) -> None:
    Sweep = ParametricSweepFactory.create(**basic_sweep_config)
    sweep_cls = cast(Any, Sweep)
    assert sweep_cls._element_source is ParamSource
    assert sweep_cls._collection_output is FloatDataCollection
    assert issubclass(Sweep, DataSource)
    assert sweep_cls._vars == {"t": RangeSpec(0.0, 1.0, steps=4)}
    assert sweep_cls.output_data_type() is FloatDataCollection
    assert sweep_cls.get_created_keys() == ["t_values"]


def test_processor_runs_and_updates_context() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=3)},
        parametric_expressions={"value": "2*t"},
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context
    assert [item.data for item in data] == [0.0, 1.0, 2.0]
    assert np.allclose(context.get_value("t_values"), np.linspace(0.0, 1.0, 3))


def test_empty_vars_raises_error(basic_sweep_config) -> None:
    config = basic_sweep_config.copy()
    config["vars"] = {}
    with pytest.raises(ValueError, match="vars must be non-empty"):
        ParametricSweepFactory.create(**config)


def test_explicit_sequence() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": SequenceSpec([1.0, 2.0, 3.0])},
        parametric_expressions={"value": "value"},
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context
    assert [item.data for item in data] == [1.0, 2.0, 3.0]
    assert context.get_value("value_values") == [1.0, 2.0, 3.0]


def test_from_context_sequence() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": FromContext("vals")},
        parametric_expressions={"value": "value"},
    )
    ctx = ContextType()
    ctx.set_value("vals", [0.0, 1.0])
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ctx))
    data = cast(FloatDataCollection, payload.data)
    assert [item.data for item in data] == [0.0, 1.0]


def test_from_context_missing_key() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": FromContext("vals")},
        parametric_expressions={"value": "value"},
    )
    pipeline = Pipeline([{"processor": Sweep}])
    with pytest.raises(KeyError):
        pipeline.process(Payload(NoDataType(), ContextType()))


def test_mixed_sequence_and_range_zip_mode() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={
            "value": SequenceSpec([1.0, 2.0, 3.0]),
            "t": RangeSpec(0.0, 2.0, steps=3),
        },
        parametric_expressions={"value": "value"},
        mode="zip",
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    assert [item.data for item in data] == [1.0, 2.0, 3.0]


def test_length_mismatch_raises_error() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1, 2]), "b": SequenceSpec([3])},
        parametric_expressions={"value": "a"},
        mode="zip",
    )
    pipeline = Pipeline([{"processor": Sweep}])
    with pytest.raises(ValueError, match="identical lengths"):
        pipeline.process(Payload(NoDataType(), ContextType()))


def test_zip_mode_broadcast() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0, 3.0]), "b": SequenceSpec([10.0])},
        parametric_expressions={"value": "a + b"},
        mode="zip",
        broadcast=True,
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    assert [item.data for item in data] == [11.0, 12.0, 13.0]


def test_include_independent_pass_through() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": SequenceSpec([5.0, 6.0])},
        parametric_expressions={},
        include_independent=True,
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    assert [item.data for item in data] == [5.0, 6.0]


def test_product_mode_basic() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0]), "b": SequenceSpec([10.0, 20.0])},
        parametric_expressions={"value": "a + b"},
        mode="product",
    )
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    expected_values = [11.0, 21.0, 12.0, 22.0]
    assert [item.data for item in data] == expected_values


def test_product_mode_from_context() -> None:
    Sweep = ParametricSweepFactory.create(
        element=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": FromContext("vals"), "b": SequenceSpec([10.0, 20.0])},
        parametric_expressions={"value": "a + b"},
        mode="product",
    )
    ctx = ContextType()
    ctx.set_value("vals", [1.0, 2.0])
    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ctx))
    data = cast(FloatDataCollection, payload.data)
    assert len(data) == 4
    expected = [11.0, 21.0, 12.0, 22.0]
    assert [item.data for item in data] == expected
