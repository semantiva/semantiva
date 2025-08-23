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

"""Tests for parametric sweep YAML configuration."""

import pytest
import yaml
import numpy as np

from semantiva.pipeline import Pipeline, Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import FloatDataCollection


@pytest.fixture
def empty_context():
    """Pytest fixture for providing an empty context."""
    return ContextType()


def test_parametric_sweep_yaml(empty_context):
    """Test parametric sweep configuration in YAML."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 5
        independent_vars:
          t: [0.0, 1.0]
        parametric_expressions:
          value: "t*2"
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)

    # Test execution
    payload = pipeline.process(Payload(NoDataType(), empty_context))
    # Verify the processor was created correctly after instantiation
    processor_class = pipeline.nodes[0].processor.__class__
    assert "ParametricSweep" in processor_class.__name__
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 5

    # Check that parameter values are in context
    assert "t_values" in context.keys()
    t_values = context.get_value("t_values")
    assert np.allclose(t_values, np.linspace(0.0, 1.0, 5))


def test_multi_variable_sweep(empty_context):
    """Test parametric sweep with multiple variables."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 4
        independent_vars:
          x: [0.0, 1.0]
          y: [2.0, 3.0]
        parametric_expressions:
          value: "x+y"
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)

    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 4

    # Check that both parameter sequences are in context
    assert "x_values" in context.keys()
    assert "y_values" in context.keys()

    x_values = context.get_value("x_values")
    y_values = context.get_value("y_values")

    assert np.allclose(x_values, np.linspace(0.0, 1.0, 4))
    assert np.allclose(y_values, np.linspace(2.0, 3.0, 4))


def test_sweep_with_static_params(empty_context):
    """Test parametric sweep with static parameters."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 3
        independent_vars:
          t: [0.0, 2.0]
        parametric_expressions:
          value: "t"
        static_params:
          offset: 10.0
          gain: 2.5
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)

    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3

    # Check that only sweep variables are in context (not static params)
    assert "t_values" in context.keys()
    assert "offset_values" not in context.keys()
    assert "gain_values" not in context.keys()


def test_sweep_no_expressions(empty_context):
    """Test parametric sweep without expressions (should work)."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 3
        independent_vars:
          t: [0.0, 1.0]
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)

    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3
    assert "t_values" in context.keys()


def test_sweep_invalid_num_steps():
    """Test that invalid num_steps raises appropriate error."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 1
        independent_vars:
          t: [0.0, 1.0]
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    # Should fail during pipeline creation

    with pytest.raises(ValueError, match="num_steps must be an integer greater than 1"):
        Pipeline(node_configs)


def test_sweep_invalid_vars_format():
    """Test that invalid variable format raises appropriate error."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 3
        independent_vars:
          t: [0.0]  # Missing max value
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    # Should fail during pipeline creation

    with pytest.raises(ValueError, match="must have range format"):
        Pipeline(node_configs)


def test_sweep_missing_required_params():
    """Test that missing required parameters falls back to standard resolution."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        # Missing num_steps and independent_vars
        parametric_expressions:
          value: "42"
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    # Should fail with standard class resolution error since structured processing fails

    with pytest.raises(ValueError, match="not found"):
        Pipeline(node_configs).process(Payload(NoDataType(), empty_context))


def test_complex_sweep_example(empty_context):
    """Test a complex example similar to the user's request."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "sweep:FloatMockDataSource:FloatDataCollection"
      parameters:
        num_steps: 3
        independent_vars:
          t: [-1, 2]
        parametric_expressions:
          x_0: "50 + 5 * t"
          y_0: "50 + 5 * t + 5 * t ** 2"
          amplitude: "100"
          angle: "60 + 5 * t"
        static_params:
          image_size: [128, 128]
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)

    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data, context = payload.data, payload.context

    assert isinstance(data, FloatDataCollection)
    assert len(data) == 3

    # Check parameter values
    assert "t_values" in context.keys()
    t_values = context.get_value("t_values")
    assert np.allclose(t_values, np.linspace(-1, 2, 3))  # [-1, 0.5, 2]
