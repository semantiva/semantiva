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

from semantiva import Pipeline, Payload, load_pipeline_from_yaml
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.workflows import ModelFittingContextProcessor, PolynomialFittingModel


def test_pipeline_model_fitting_from_yaml():
    nodes = load_pipeline_from_yaml("tests/pipeline_model_fitting.yaml")
    pipeline = Pipeline(nodes)

    context = ContextType(
        {
            "t_values": [0.0, 1.0, 2.0],
            "data_values": [1.0, 3.0, 7.0],
        }
    )
    payload = Payload(NoDataType(), context)
    result = pipeline.process(payload)

    node = pipeline.nodes[0]
    assert isinstance(node.processor, ModelFittingContextProcessor)
    assert isinstance(node.processor.fitting_model, PolynomialFittingModel)
    assert node.processor.fitting_model.degree == 2
    assert "fit_coefficients" in result.context.keys()
