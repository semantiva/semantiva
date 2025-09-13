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

"""Tests that sweep exposes required and created context keys."""

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    FromContext,
)
from semantiva.examples.test_utils import FloatDataCollection, FloatValueDataSource
from semantiva.inspection.builder import build_pipeline_inspection


def test_required_and_created_keys() -> None:
    Sweep = ParametricSweepFactory.create(
        element=FloatValueDataSource,
        collection_output=FloatDataCollection,
        vars={"v": FromContext("vals")},
        parametric_expressions={"value": "v"},
    )
    inspection = build_pipeline_inspection([{"processor": Sweep}])
    node_info = inspection.nodes[0]
    assert "vals" in inspection.required_context_keys
    assert "v_values" in node_info.created_keys
