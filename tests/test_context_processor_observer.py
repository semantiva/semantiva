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

"""
Observer pattern tests for context processors.

Tests stateless context processor operation via observer-mediated updates,
parameter resolution precedence (config > context > defaults), and
metadata extraction from processor signatures.
"""

from semantiva.context_processors.context_processors import ContextProcessor
from semantiva.context_processors.context_types import ContextType
from semantiva.pipeline.nodes._pipeline_node_factory import _PipelineNodeFactory
from semantiva.workflows import ModelFittingContextProcessor, PolynomialFittingModel
from semantiva.data_types import NoDataType
from semantiva.pipeline import Payload


class SetPair(ContextProcessor):
    def _process_logic(self, *, a: int = 1, b: int = 2) -> None:
        self._notify_context_update("pair.a", a)
        self._notify_context_update("pair.b", b)

    @classmethod
    def context_keys(cls):
        return ["pair.a", "pair.b"]


def test_observer_updates_and_metadata():
    ctx = ContextType()
    node = _PipelineNodeFactory.create_context_processor_wrapper_node(SetPair, {})
    node.process(Payload(NoDataType(), ctx))
    assert ctx.get_value("pair.a") == 1
    assert ctx.get_value("pair.b") == 2
    md = SetPair.get_metadata()["parameters"]
    assert list(md.keys()) == ["a", "b"]
    assert md["a"].default == 1


def test_node_parameter_resolution_precedence():
    ctx = ContextType({"a": 5, "b": 6})
    node = _PipelineNodeFactory.create_context_processor_wrapper_node(
        SetPair, {"a": 10}
    )
    node.process(Payload(NoDataType(), ctx))
    assert ctx.get_value("pair.a") == 10
    assert ctx.get_value("pair.b") == 6


def test_factory_binding_model_fitting():
    Bound = ModelFittingContextProcessor.with_context_keyword("fit.coeff")
    model = PolynomialFittingModel(1)
    node = _PipelineNodeFactory.create_context_processor_wrapper_node(
        Bound, {"fitting_model": model}
    )
    ctx = ContextType({"x_values": [0, 1], "y_values": [1, 2]})
    node.process(Payload(NoDataType(), ctx))
    assert "fit.coeff" in ctx.keys()
    assert Bound.get_created_keys() == ["fit.coeff"]
