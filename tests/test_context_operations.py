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
from typing import List
from semantiva.context_processors import ContextProcessor
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.pipeline import Payload
from semantiva.pipeline.nodes._pipeline_node_factory import _PipelineNodeFactory
from semantiva.workflows import FittingModel, ModelFittingContextProcessor


class MockFittingModel(FittingModel):
    def fit(self, independent_variable, dependent_variable):
        return {"fit_results": "mock_results"}


class MockContextProcessor(ContextProcessor):
    def _process_logic(self, *, required_key: str) -> None:
        self._notify_context_update("operation_result", required_key)

    @classmethod
    def context_keys(cls) -> List[str]:
        return ["operation_result"]


def test_mock_context_processor():
    context = ContextType({"required_key": "value"})
    node = _PipelineNodeFactory.create_context_processor_wrapper_node(
        MockContextProcessor, {}
    )
    payload = node.process(Payload(NoDataType(), context))
    assert payload.context.get_value("operation_result") == "value"


def test_model_fitting_context_processor():
    context = ContextType({"x_values": [1, 2, 3], "y_values": [4, 5, 6]})
    fitting_model = MockFittingModel()
    Bound = ModelFittingContextProcessor.with_context_keyword("fit_results")
    node = _PipelineNodeFactory.create_context_processor_wrapper_node(
        Bound, {"fitting_model": fitting_model}
    )
    result = node.process(Payload(NoDataType(), context))
    assert result.context.get_value("fit_results") == {"fit_results": "mock_results"}

    with pytest.raises(ValueError):
        incomplete_context = ContextType({"x_values": None, "y_values": [1, 2, 3]})
        node.process(Payload(NoDataType(), incomplete_context))


if __name__ == "__main__":
    pytest.main()
