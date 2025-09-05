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
Tests for invalid parameter detection in data IO operations.
"""

import inspect

from semantiva.data_processors.io_operation_factory import _IOOperationFactory
from semantiva.pipeline._param_resolution import classify_unknown_config_params
from semantiva.examples.test_utils import (
    FloatValueDataSource,
    FloatTxtFileSaver,
)


class TestInvalidParameterDetectionDataIO:
    """Test that invalid parameter detection works for all data IO types."""

    def test_data_source_signature_exact_match(self):
        """DataSource should have exact signature matching _get_data."""
        data_op = _IOOperationFactory.create_data_operation(FloatValueDataSource)
        sig = inspect.signature(data_op._process_logic)

        # Should have self, data, value parameters
        param_names = list(sig.parameters.keys())
        assert param_names == ["self", "data", "value"]

        # Should not have **kwargs
        has_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        assert not has_kwargs

    def test_data_sink_signature_exact_match(self):
        """DataSink should have exact signature matching _send_data (excluding data param)."""
        data_op = _IOOperationFactory.create_data_operation(FloatTxtFileSaver)
        sig = inspect.signature(data_op._process_logic)

        # Should have self, data, path parameters
        param_names = list(sig.parameters.keys())
        assert param_names == ["self", "data", "path"]

        # Should not have **kwargs
        has_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        assert not has_kwargs

    def test_data_source_invalid_param_detection(self):
        """DataSource should detect invalid parameters."""
        data_op = _IOOperationFactory.create_data_operation(FloatValueDataSource)

        # Test with invalid parameters
        config = {
            "value": 42.0,  # Valid
            "invalid_param": True,  # Invalid
            "another_invalid": "test",  # Invalid
        }

        issues = classify_unknown_config_params(
            processor_cls=data_op, processor_config=config
        )

        assert len(issues) == 2
        invalid_names = [issue["name"] for issue in issues]
        assert "invalid_param" in invalid_names
        assert "another_invalid" in invalid_names

    def test_data_sink_invalid_param_detection(self):
        """DataSink should detect invalid parameters."""
        data_op = _IOOperationFactory.create_data_operation(FloatTxtFileSaver)

        # Test with invalid parameters
        config = {
            "path": "test.txt",  # Valid
            "invalid_param": True,  # Invalid
        }

        issues = classify_unknown_config_params(
            processor_cls=data_op, processor_config=config
        )

        assert len(issues) == 1
        assert issues[0]["name"] == "invalid_param"

    def test_all_valid_params_accepted(self):
        """All data IO types should accept valid parameters without issues."""
        test_cases = [
            (FloatValueDataSource, {"value": 25.0}),
            (FloatTxtFileSaver, {"path": "output.txt"}),
        ]

        for data_io_class, valid_config in test_cases:
            data_op = _IOOperationFactory.create_data_operation(data_io_class)
            issues = classify_unknown_config_params(
                processor_cls=data_op, processor_config=valid_config
            )

            assert (
                len(issues) == 0
            ), f"Should not have issues for valid config in {data_io_class.__name__}: {issues}"
