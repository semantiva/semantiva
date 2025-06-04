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
from semantiva.examples.test_utils import (
    FloatDataCollection,
    FloatDataType,
    FloatCollectValueProbe,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel
from semantiva.context_processors.context_processors import ModelFittingContextProcessor
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.data_processors.data_slicer_factory import Slicer


@pytest.fixture
def linear_int_data_collection(num_items=5):
    """Create a collection of FloatDataType objects with linear data."""
    data_collection = FloatDataCollection()
    for i in range(num_items):
        data_collection.append(FloatDataType(float(i)))
    return data_collection


def test_pipeline_single_string_key(linear_int_data_collection):
    """Test a pipeline with a single string key."""
    t_values = [i for i in range(len(linear_int_data_collection))]
    node_configurations = [
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
            "context_keyword": "data_values",
        },
        {
            "processor": ModelFittingContextProcessor,
            "parameters": {
                "fitting_model": PolynomialFittingModel(degree=1),
                "independent_var_key": "t_values",
                "dependent_var_key": "data_values",
                "context_keyword": "fit_coefficients",
            },
        },
    ]
    pipeline = Pipeline(node_configurations)
    context_dict = {"t_values": t_values}
    _, output_context = pipeline.process(linear_int_data_collection, context_dict)
    assert "fit_coefficients" in output_context.keys()
    print(output_context.get_value("fit_coefficients"))
