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
from semantiva.examples.test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatDataType,
)


def test_data_operation_context_injector_injects_result():
    node = _PipelineNodeFactory.create_data_operation_context_injector_probe_node(
        processor_cls=FloatMultiplyOperation,
        context_keyword="mask",
        factor=2,
    )
    data = FloatDataType(5.0)
    ctx = ContextType()
    result = node.process(Payload(data, ctx))
    assert result.data is data
    assert result.context is ctx
    assert ctx.get_value("mask").data == 10.0


def test_data_operation_context_injector_rejects_probe_class():
    with pytest.raises(ValueError):
        _PipelineNodeFactory.create_data_operation_context_injector_probe_node(
            processor_cls=FloatCollectValueProbe,
            context_keyword="mask",
        )


@pytest.mark.parametrize("keyword", ["", 123])
def test_data_operation_context_injector_bad_keyword(keyword):
    with pytest.raises(ValueError):
        _PipelineNodeFactory.create_data_operation_context_injector_probe_node(
            processor_cls=FloatMultiplyOperation,
            context_keyword=keyword,
        )
