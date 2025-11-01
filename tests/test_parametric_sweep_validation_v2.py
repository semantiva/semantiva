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

from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
)
from semantiva.examples.test_utils import FloatDataCollection, FloatDataType


class ValidSource(DataSource):
    @classmethod
    def output_data_type(cls):
        return FloatDataType

    @classmethod
    def _get_data(cls, a: float, b: int):
        return object()


def test_unknown_expr_key_raises_typeerror():
    with pytest.raises(TypeError):
        ParametricSweepFactory.create(
            element=ValidSource,
            element_kind="DataSource",
            collection_output=FloatDataCollection,
            vars={"t": RangeSpec(0.0, 1.0, steps=2)},
            parametric_expressions={"unknown": "t"},
        )


def test_missing_required_is_exposed():
    Sweep = ParametricSweepFactory.create(
        element=ValidSource,
        element_kind="DataSource",
        collection_output=FloatDataCollection,
        vars={"t": RangeSpec(0.0, 1.0, steps=2)},
        parametric_expressions={"a": "t"},
    )
    sig = inspect.signature(Sweep._get_data)
    assert "b" in sig.parameters
