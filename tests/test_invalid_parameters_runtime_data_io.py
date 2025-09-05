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
Tests for runtime enforcement of invalid parameters in data IO operations.
"""

import pytest
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.exceptions import InvalidNodeParameterError
from semantiva.examples.test_utils import (
    FloatValueDataSource,
    FloatTxtFileSaver,
    FloatMultiplyOperation,
)


def test_runtime_raises_on_invalid_data_source_param():
    """Runtime should raise InvalidNodeParameterError for DataSource with invalid params."""
    config = {
        "processor": FloatValueDataSource,
        "parameters": {
            "value": 42.0,  # Valid
            "invalid_param": "not_allowed",  # Invalid
        },
    }

    with pytest.raises(InvalidNodeParameterError) as exc_info:
        _pipeline_node_factory(config)

    error = exc_info.value
    assert "invalid_param" in str(error)
    assert "FloatValueDataSource" in error.processor_fqcn


def test_runtime_raises_on_invalid_data_sink_param():
    """Runtime should raise InvalidNodeParameterError for DataSink with invalid params."""
    config = {
        "processor": FloatTxtFileSaver,
        "parameters": {"path": "test.txt", "invalid_param": True},  # Valid  # Invalid
    }

    with pytest.raises(InvalidNodeParameterError) as exc_info:
        _pipeline_node_factory(config)

    error = exc_info.value
    assert "invalid_param" in str(error)
    assert "FloatTxtFileSaver" in error.processor_fqcn


def test_runtime_raises_on_invalid_operation_param():
    """Runtime should raise InvalidNodeParameterError for DataOperation with invalid params."""
    config = {
        "processor": FloatMultiplyOperation,
        "parameters": {"factor": 2.0, "invalid_param": "test"},  # Valid  # Invalid
    }

    with pytest.raises(InvalidNodeParameterError) as exc_info:
        _pipeline_node_factory(config)

    error = exc_info.value
    assert "invalid_param" in str(error)
    assert "FloatMultiplyOperation" in error.processor_fqcn


def test_runtime_accepts_valid_params():
    """Runtime should accept valid parameters for all operation types."""
    configs = [
        {"processor": FloatValueDataSource, "parameters": {"value": 25.5}},
        {"processor": FloatTxtFileSaver, "parameters": {"path": "output.txt"}},
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 3.0}},
    ]

    for config in configs:
        # Should not raise an exception
        node = _pipeline_node_factory(config)
        assert node is not None


def test_inspection_detects_data_io_invalid_params():
    """Inspection should detect invalid parameters in data IO operations."""
    from semantiva.inspection import build_pipeline_inspection

    configs = [
        {
            "processor": FloatValueDataSource,
            "parameters": {
                "value": 42.0,  # Valid
                "invalid_param1": True,  # Invalid
                "invalid_param2": "test",  # Invalid
            },
        }
    ]

    inspection = build_pipeline_inspection(configs)

    # Check the first node
    first_node = inspection.nodes[0]
    assert not first_node.is_configuration_valid
    assert len(first_node.invalid_parameters) == 2

    invalid_names = [issue["name"] for issue in first_node.invalid_parameters]
    assert "invalid_param1" in invalid_names
    assert "invalid_param2" in invalid_names
