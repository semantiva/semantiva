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

from typing import Any, cast
import numpy as np
import pytest

from semantiva.context_processors.context_types import ContextType
from semantiva.data_io import DataSource
from semantiva.data_processors.parametric_sweep_factory import ParametricSweepFactory
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
        "independent_vars": {"t": (0.0, 1.0)},
        "parametric_expressions": {"value": "t"},
        "num_steps": 4,
    }


def test_factory_creates_processor(basic_sweep_config) -> None:
    """Test that factory creates a processor with correct attributes and types."""
    Sweep = ParametricSweepFactory.create(**basic_sweep_config)
    sweep_cls = cast(Any, Sweep)

    # Verify factory-created attributes
    assert sweep_cls._element_source is ParamSource
    assert sweep_cls._collection_output is FloatDataCollection
    assert sweep_cls._independent_vars == {"t": (0.0, 1.0)}
    assert sweep_cls._parametric_expressions == {"value": "t"}
    assert sweep_cls._num_steps == 4

    # Verify processor interface
    assert Sweep.input_data_type() is NoDataType
    assert Sweep.output_data_type() is FloatDataCollection
    assert Sweep.get_created_keys() == ["t_values"]


def test_processor_runs_and_updates_context() -> None:
    """Test basic linear parametric sweep execution and context updates."""
    generator = ParametricSweepFactory.create(
        element_source=ParamSource,
        collection_output=FloatDataCollection,
        independent_vars={"t": (0.0, 1.0)},
        parametric_expressions={"value": "2*t"},
        num_steps=3,
    )

    pipeline = Pipeline([{"processor": generator}])
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data, context = payload.data, payload.context

    # Verify output data
    assert isinstance(data, FloatDataCollection)
    assert [item.data for item in data] == [0.0, 1.0, 2.0]

    # Verify context contains parameter values
    assert np.allclose(context.get_value("t_values"), np.linspace(0.0, 1.0, 3))


def test_empty_independent_vars_raises_error(basic_sweep_config) -> None:
    """Test that empty independent_vars raises ValueError."""
    config = basic_sweep_config.copy()
    config["independent_vars"] = {}

    with pytest.raises(ValueError, match="independent_vars must be non-empty"):
        ParametricSweepFactory.create(**config)
