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
"""Tests for ParametricSweepFactory."""

from typing import Any, cast, Dict, Union
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
def invalid_data_source():
    """Fixture providing an invalid DataSource class for testing."""

    class NotDataSource:
        pass

    return NotDataSource


@pytest.fixture
def invalid_collection():
    """Fixture providing an invalid collection class for testing."""

    class NotCollection:
        pass

    return NotCollection


@pytest.fixture
def basic_sweep_config():
    """Fixture providing basic valid configuration for sweep creation."""
    return {
        "element_source": ParamSource,
        "collection_output": FloatDataCollection,
        "vars": {"t": RangeSpec(0.0, 1.0, steps=4)},
        "parametric_expressions": {"value": "t"},
    }


def test_factory_creates_processor(basic_sweep_config) -> None:
    """Test that factory creates a processor with correct attributes and types."""
    Sweep = ParametricSweepFactory.create(**basic_sweep_config)
    sweep_cls = cast(Any, Sweep)

    # Verify factory-created attributes
    assert sweep_cls._element_source is ParamSource
    assert sweep_cls._collection_output is FloatDataCollection
    assert sweep_cls._vars == {"t": RangeSpec(0.0, 1.0, steps=4)}
    assert sweep_cls._parametric_expressions == {"value": "t"}
    assert sweep_cls._mode == "product"  # Default mode

    # Verify processor interface
    assert Sweep.input_data_type() is NoDataType
    assert Sweep.output_data_type() is FloatDataCollection
    assert Sweep.get_created_keys() == ["t_values"]


def test_processor_runs_and_updates_context() -> None:
    """Test basic linear parametric sweep execution and context updates."""
    generator = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=3)},
        parametric_expressions={"value": "2*t"},
    )

    pipeline = Pipeline([{"processor": generator}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data, context = payload.data, payload.context

    # Verify output data (product mode produces 3 elements)
    assert isinstance(data, FloatDataCollection)
    assert [item.data for item in data] == [0.0, 1.0, 2.0]

    # Verify context contains parameter values
    assert np.allclose(context.get_value("t_values"), np.linspace(0.0, 1.0, 3))


def test_empty_vars_raises_error(basic_sweep_config) -> None:
    """Test that empty vars raises ValueError."""
    config = basic_sweep_config.copy()
    config["vars"] = {}

    with pytest.raises(ValueError, match="vars must be non-empty"):
        ParametricSweepFactory.create(**config)


def test_explicit_sequence() -> None:
    """Explicit sequences are used as-is."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
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
    """Sequences can be pulled from the context at runtime."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
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


def test_mixed_sequence_and_range_zip_mode() -> None:
    """Mixed sequences and ranges work in zip mode with identical lengths."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
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
    context = payload.context
    assert [item.data for item in data] == [1.0, 2.0, 3.0]
    assert np.allclose(context.get_value("t_values"), np.linspace(0.0, 2.0, 3))


def test_length_mismatch_raises_error() -> None:
    """All explicit sequences must have identical length in zip mode without broadcast."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1, 2]), "b": SequenceSpec([3])},
        parametric_expressions={"value": "a"},
        mode="zip",
    )
    with pytest.raises(ValueError, match="identical lengths"):
        Sweep.run(NoDataType())


def test_zip_mode_broadcast() -> None:
    """Zip mode with broadcast allows different sequence lengths."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0, 3.0]), "b": SequenceSpec([10.0])},
        parametric_expressions={"value": "a + b"},
        mode="zip",
        broadcast=True,
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    # b should be repeated: [10.0, 10.0, 10.0]
    assert [item.data for item in data] == [11.0, 12.0, 13.0]


def test_range_spec_validation() -> None:
    """RangeSpec validates its parameters."""
    # Valid range spec
    spec = RangeSpec(0.0, 1.0, steps=5)
    assert spec.lo == 0.0
    assert spec.hi == 1.0
    assert spec.steps == 5

    # Invalid steps
    with pytest.raises(ValueError, match="steps must be positive"):
        RangeSpec(0.0, 1.0, steps=0)

    # Invalid scale for log
    with pytest.raises(ValueError, match="log scale requires positive bounds"):
        RangeSpec(-1.0, 1.0, steps=5, scale="log")


def test_sequence_spec_validation() -> None:
    """SequenceSpec validates its parameters."""
    # Valid sequence spec
    spec = SequenceSpec([1, 2, 3])
    assert list(spec.values) == [1, 2, 3]

    # Empty sequence
    with pytest.raises(ValueError, match="values must be non-empty"):
        SequenceSpec([])

    # String sequence (not allowed)
    with pytest.raises(TypeError, match="values must be a non-string sequence"):
        SequenceSpec("abc")


def test_from_context_errors() -> None:
    """Missing context observer or bad context values raise errors."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": FromContext("vals")},
        parametric_expressions={"value": "value"},
    )

    op = Sweep()
    with pytest.raises(RuntimeError):
        op.process(NoDataType())

    ctx = ContextType()
    pipeline = Pipeline([{"processor": Sweep}])
    with pytest.raises(ValueError):
        pipeline.process(Payload(NoDataType(), ctx))
    ctx.set_value("vals", "bad")
    with pytest.raises(TypeError):
        pipeline.process(Payload(NoDataType(), ctx))


def test_include_independent_pass_through() -> None:
    """include_independent passes current values directly to DataSource."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
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
    """Product mode generates Cartesian product of all variables."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0]), "b": SequenceSpec([10.0, 20.0])},
        parametric_expressions={"value": "a + b"},
        mode="product",
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    # Should produce 4 combinations: (1,10), (1,20), (2,10), (2,20)
    expected_values = [11.0, 21.0, 12.0, 22.0]  # a + b for each combination
    assert [item.data for item in data] == expected_values
    assert context.get_value("a_values") == [1.0, 2.0]
    assert context.get_value("b_values") == [10.0, 20.0]


def test_product_mode_with_ranges() -> None:
    """Product mode expands ranges and combines with sequences."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"a": SequenceSpec([1.0, 2.0]), "t": RangeSpec(0.0, 1.0, steps=2)},
        parametric_expressions={"value": "a * t"},
        mode="product",
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    # t expanded to [0.0, 1.0], combined with a=[1.0, 2.0]
    # Combinations: (1,0), (1,1), (2,0), (2,1)
    expected_values = [0.0, 1.0, 0.0, 2.0]  # a * t for each combination
    assert [item.data for item in data] == expected_values
    assert context.get_value("a_values") == [1.0, 2.0]
    assert np.allclose(context.get_value("t_values"), [0.0, 1.0])


def test_product_mode_three_variables() -> None:
    """Product mode with three variables generates correct number of combinations."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={
            "a": SequenceSpec([1.0, 2.0]),
            "b": SequenceSpec([10.0]),
            "c": SequenceSpec([100.0, 200.0, 300.0]),
        },
        parametric_expressions={"value": "a + b + c"},
        mode="product",
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)

    # Should produce 2 × 1 × 3 = 6 combinations
    assert len(data) == 6
    # First few combinations: (1,10,100), (1,10,200), (1,10,300), (2,10,100), ...
    expected_values = [111.0, 211.0, 311.0, 112.0, 212.0, 312.0]  # a + b + c for each
    assert [item.data for item in data] == expected_values


def test_product_mode_from_context() -> None:
    """Product mode works with FromContext sequences."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
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

    # Should produce 2 × 2 = 4 combinations
    assert len(data) == 4
    expected_values = [11.0, 21.0, 12.0, 22.0]  # a + b for each combination
    assert [item.data for item in data] == expected_values


def test_product_mode_range_only() -> None:
    """Product mode with only ranges."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"x": RangeSpec(0.0, 1.0, steps=2), "y": RangeSpec(10.0, 20.0, steps=2)},
        parametric_expressions={"value": "x + y"},
        mode="product",
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    # Should produce 2 × 2 = 4 combinations
    assert len(data) == 4
    # x expanded to [0.0, 1.0], y expanded to [10.0, 20.0]
    expected_combinations = [(0.0, 10.0), (0.0, 20.0), (1.0, 10.0), (1.0, 20.0)]
    expected_values = [x + y for x, y in expected_combinations]
    assert [item.data for item in data] == expected_values
    assert np.allclose(context.get_value("x_values"), [0.0, 1.0])
    assert np.allclose(context.get_value("y_values"), [10.0, 20.0])


def test_product_mode_include_independent() -> None:
    """Product mode with include_independent passes variables to DataSource."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"value": SequenceSpec([1.0, 2.0])},
        parametric_expressions={},
        mode="product",
        include_independent=True,
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)

    # Should use the 'value' parameter directly since include_independent=True
    # and no parametric_expressions override it
    assert len(data) == 2  # 2 combinations
    assert [item.data for item in data] == [1.0, 2.0]


def test_invalid_mode_raises_error() -> None:
    """Invalid mode parameter raises ValueError."""
    with pytest.raises(ValueError, match="mode must be 'zip' or 'product'"):
        ParametricSweepFactory.create(
            element_source=ParamSource,
            collection_output=FloatDataCollection,
            vars={"a": SequenceSpec([1, 2])},
            parametric_expressions={"value": "a"},
            mode="invalid",
        )


def test_zip_vs_product_mode_comparison() -> None:
    """Demonstrates the difference between zip and product modes with identical inputs."""
    vars_config: Dict[str, Union[RangeSpec, SequenceSpec, FromContext]] = {
        "a": SequenceSpec([1.0, 2.0]),
        "b": SequenceSpec([10.0, 20.0]),
    }
    parametric_expressions = {"value": "a + b"}

    # Zip mode: pairs elements (1,10), (2,20)
    ZipSweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars=vars_config,
        parametric_expressions=parametric_expressions,
        mode="zip",
    )
    zip_pipeline = Pipeline([{"processor": ZipSweep}])
    zip_payload = zip_pipeline.process(Payload(NoDataType(), ContextType()))
    zip_data = cast(FloatDataCollection, zip_payload.data)

    # Product mode: all combinations (1,10), (1,20), (2,10), (2,20)
    ProductSweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars=vars_config,
        parametric_expressions=parametric_expressions,
        mode="product",
    )
    product_pipeline = Pipeline([{"processor": ProductSweep}])
    product_payload = product_pipeline.process(Payload(NoDataType(), ContextType()))
    product_data = cast(FloatDataCollection, product_payload.data)

    # Verify different results
    assert len(zip_data) == 2  # zip produces 2 elements
    assert len(product_data) == 4  # product produces 2×2=4 elements

    zip_values = [item.data for item in zip_data]
    product_values = [item.data for item in product_data]

    assert zip_values == [11.0, 22.0]  # (1+10), (2+20)
    assert product_values == [11.0, 21.0, 12.0, 22.0]  # (1+10), (1+20), (2+10), (2+20)


def test_range_spec_linear_scale() -> None:
    """RangeSpec with linear scale generates correct values."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=3, scale="linear")},
        parametric_expressions={"value": "t"},
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    expected_values = [0.0, 0.5, 1.0]
    assert [item.data for item in data] == expected_values
    assert np.allclose(context.get_value("t_values"), expected_values)


def test_range_spec_log_scale() -> None:
    """RangeSpec with log scale generates correct values."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(1.0, 100.0, steps=3, scale="log")},
        parametric_expressions={"value": "t"},
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    expected_values = [1.0, 10.0, 100.0]  # 10^0, 10^1, 10^2
    assert np.allclose([item.data for item in data], expected_values)
    assert np.allclose(context.get_value("t_values"), expected_values)


def test_range_spec_endpoint_false() -> None:
    """RangeSpec with endpoint=False excludes the upper bound."""
    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=4, endpoint=False)},
        parametric_expressions={"value": "t"},
    )

    pipeline = Pipeline([{"processor": Sweep}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data = cast(FloatDataCollection, payload.data)
    context = payload.context

    # endpoint=False should give [0, 0.25, 0.5, 0.75] (excluding 1.0)
    expected_values = [0.0, 0.25, 0.5, 0.75]
    assert np.allclose([item.data for item in data], expected_values)
    assert np.allclose(context.get_value("t_values"), expected_values)


def test_invalid_var_spec_type() -> None:
    """Invalid variable specification type raises TypeError."""

    class InvalidSpec:
        pass

    Sweep = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        vars={"invalid": InvalidSpec()},  # type: ignore
        parametric_expressions={"value": "invalid"},
    )

    with pytest.raises(TypeError, match="Invalid specification for variable"):
        Sweep.run(NoDataType())
