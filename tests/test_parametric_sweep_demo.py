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

"""Tests for parametric sweep demo YAML files."""

import numpy as np
from pathlib import Path

from semantiva import Pipeline, Payload, load_pipeline_from_yaml
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import FloatDataType


def test_parametric_sweep_demo_yaml():
    """Test the parametric sweep demo YAML file."""

    # Get the path to the demo YAML file
    test_dir = Path(__file__).parent
    yaml_file = test_dir / "parametric_sweep_demo.yaml"

    # Load and execute the pipeline
    node_configurations = load_pipeline_from_yaml(str(yaml_file))
    pipeline = Pipeline(node_configurations)

    # Process the pipeline
    payload = pipeline.process(Payload(NoDataType(), ContextType()))
    data, context = payload.data, payload.context

    # Verify the output
    assert isinstance(data, FloatDataType), "Output should be FloatDataType"

    # Verify context contains expected keys
    assert "t_values" in context.keys(), "Context should contain sweep parameter values"
    assert (
        "sweep_results" in context.keys()
    ), "Context should contain collected sweep data"
    assert "final_sum" in context.keys(), "Context should contain final result"

    # Verify parameter values
    t_values = context.get_value("t_values")
    assert np.allclose(t_values, np.linspace(-1, 2, 3))

    final_result = context.get_value("final_sum")
    assert final_result["value"] == 3.0

    # Verify that sweep_results contains the slicer output (a list of collected values)
    sweep_results = context.get_value("sweep_results")
    assert isinstance(sweep_results, list), "Sweep results should be a list from slicer"
    assert len(sweep_results) == 3, "Should have 3 collected values"
