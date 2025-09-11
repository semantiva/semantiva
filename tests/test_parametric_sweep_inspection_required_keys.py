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
from semantiva.pipeline.nodes._pipeline_node_factory import _PipelineNodeFactory


def test_required_and_created_keys() -> None:
    Sweep = ParametricSweepFactory.create(
        element=FloatValueDataSource,
        collection_output=FloatDataCollection,
        vars={"v": FromContext("vals")},
        parametric_expressions={"value": "v"},
    )
    node = _PipelineNodeFactory.create_io_node({"processor": Sweep})
    assert node.processor.get_processing_parameter_names() == ["vals"]
    assert node.__class__.get_created_keys() == ["v_values"]  # type: ignore[attr-defined]
