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

"""Tests for element-source parameter validation in ParametricSweepFactory."""

import pytest

from semantiva.data_io import DataSource
from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
)
from semantiva.examples.test_utils import FloatDataType, FloatDataCollection


class ValidSource(DataSource):
    @classmethod
    def _get_data(cls, value: float, scale: float = 1.0) -> FloatDataType:
        return FloatDataType(value * scale)

    @classmethod
    def output_data_type(cls):
        return FloatDataType


def test_unknown_parameter() -> None:
    with pytest.raises(TypeError, match="not accepted"):
        ParametricSweepFactory.create(
            element=ValidSource,
            collection_output=FloatDataCollection,
            vars={"t": RangeSpec(0.0, 1.0, steps=2)},
            parametric_expressions={"bad": "t"},
        )


def test_missing_required_parameter() -> None:
    with pytest.raises(TypeError, match="requires parameters"):
        ParametricSweepFactory.create(
            element=ValidSource,
            collection_output=FloatDataCollection,
            vars={"t": RangeSpec(0.0, 1.0, steps=2)},
            parametric_expressions={},
        )
