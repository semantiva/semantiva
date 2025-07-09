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

from semantiva.pipeline.nodes._pipeline_node_factory import _PipelineNodeFactory
from semantiva.pipeline import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.data_processors import DataOperation
from semantiva.examples.test_utils import (
    FloatCollectValueProbe,
    FloatDataType,
)


class DoubleOperation(DataOperation):
    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType

    def _process_logic(self, data):
        return FloatDataType(data.data * 2)


def test_context_processor_node_operation():
    node = _PipelineNodeFactory.create_context_processor_node(
        input_context_keyword="foo",
        output_context_keyword="bar",
        processor_cls=DoubleOperation,
    )
    ctx = ContextType({"foo": FloatDataType(3.0)})
    data = FloatDataType(1.0)
    result = node.process(Payload(data, ctx))
    assert result.data is data
    assert ctx.get_value("bar").data == 6.0


def test_context_processor_node_probe():
    node = _PipelineNodeFactory.create_context_processor_node(
        input_context_keyword="foo",
        output_context_keyword="bar",
        processor_cls=FloatCollectValueProbe,
    )
    ctx = ContextType({"foo": FloatDataType(4.0)})
    data = FloatDataType(1.0)
    node.process(Payload(data, ctx))
    assert ctx.get_value("bar") == 4.0


def test_context_processor_node_overwrite():
    node = _PipelineNodeFactory.create_context_processor_node(
        input_context_keyword="foo",
        output_context_keyword="foo",
        processor_cls=DoubleOperation,
    )
    ctx = ContextType({"foo": FloatDataType(2.0)})
    node.process(Payload(FloatDataType(0.0), ctx))
    assert ctx.get_value("foo").data == 4.0


def test_context_processor_node_missing_key():
    node = _PipelineNodeFactory.create_context_processor_node(
        input_context_keyword="foo",
        output_context_keyword="bar",
        processor_cls=DoubleOperation,
    )
    with pytest.raises(KeyError):
        node.process(Payload(FloatDataType(0.0), ContextType()))


def test_context_processor_node_validation():
    with pytest.raises(ValueError):
        _PipelineNodeFactory.create_context_processor_node(
            input_context_keyword="foo",
            output_context_keyword="bar",
            processor_cls=str,
        )
    for key in ["", 123]:
        with pytest.raises(ValueError):
            _PipelineNodeFactory.create_context_processor_node(
                input_context_keyword=key,
                output_context_keyword="bar",
                processor_cls=DoubleOperation,
            )
        with pytest.raises(ValueError):
            _PipelineNodeFactory.create_context_processor_node(
                input_context_keyword="foo",
                output_context_keyword=key,
                processor_cls=DoubleOperation,
            )
