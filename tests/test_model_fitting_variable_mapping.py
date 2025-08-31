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

"""Tests for ModelFittingContextProcessor variable mapping functionality."""

import pytest
from semantiva.workflows.fitting_model import (
    ModelFittingContextProcessor,
    PolynomialFittingModel,
    _model_fitting_processor_factory,
)
from semantiva.registry.class_registry import ClassRegistry
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory


class TestModelFittingProcessorFactory:
    """Test suite for the model fitting processor factory functionality."""

    def test_factory_basic_functionality(self):
        """Test basic factory functionality with simple parameters."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="time_values",
            dependent_var_key="measurements",
            context_keyword="fit_results",
        )

        # Check parameter names
        expected_params = ["time_values", "measurements", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params

        # Check output key
        assert processor_cls.get_created_keys() == ["fit_results"]
        assert processor_cls.context_keys() == ["fit_results"]

        # Check class name generation
        assert "ModelFittingContextProcessor_MAPPED" in processor_cls.__name__
        assert "time_values" in processor_cls.__name__
        assert "measurements" in processor_cls.__name__

    def test_factory_with_nested_path(self):
        """Test factory with nested path for dependent variable."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="std_dev_coefficients",
        )

        # Check that parameter name is base (not full path)
        expected_params = ["t_values", "gaussian_fit_parameters", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params

        # Check output key
        assert processor_cls.get_created_keys() == ["std_dev_coefficients"]

    def test_factory_default_output_key(self):
        """Test factory with default output key."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="y_data",
            context_keyword="fit.parameters",
        )

        # Should use default output key
        assert processor_cls.get_created_keys() == ["fit.parameters"]
        assert processor_cls.context_keys() == ["fit.parameters"]

    def test_factory_class_docstring(self):
        """Test that factory generates appropriate docstring."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="nested.y_data",
            context_keyword="results",
        )

        docstring = processor_cls.__doc__
        assert "x_values from: x_data" in docstring
        assert "y_values from: nested.y_data" in docstring
        assert "output to: results" in docstring


class TestModelFittingWithNestedPaths:
    """Test suite for nested path extraction functionality."""

    def test_nested_path_single_dictionary(self):
        """Test nested path extraction from single dictionary."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="std_dev_coefficients",
        )

        processor = processor_cls()

        # Create test data with nested structure
        t_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        gaussian_fit_parameters = {
            "std_dev_x": [0.1, 0.2, 0.3, 0.4, 0.5],
            "std_dev_y": [0.15, 0.25, 0.35, 0.45, 0.55],
            "angle": [10, 15, 20, 25, 30],
        }
        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []

        def mock_notify_update(key, value):
            updates.append((key, value))

        processor._notify_context_update = mock_notify_update

        # Process the data
        processor._process_logic(
            t_values=t_values,
            gaussian_fit_parameters=gaussian_fit_parameters,
            fitting_model=fitting_model,
        )

        # Verify the results
        assert len(updates) == 1
        assert updates[0][0] == "std_dev_coefficients"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]

    def test_nested_path_list_of_dictionaries(self):
        """Test nested path extraction from list of dictionaries (slicer output)."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="std_dev_coefficients",
        )

        processor = processor_cls()

        # Create test data as list of dictionaries (like slicer output)
        t_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        gaussian_fit_parameters = [
            {"std_dev_x": 0.1, "std_dev_y": 0.15, "angle": 10},
            {"std_dev_x": 0.2, "std_dev_y": 0.25, "angle": 15},
            {"std_dev_x": 0.3, "std_dev_y": 0.35, "angle": 20},
            {"std_dev_x": 0.4, "std_dev_y": 0.45, "angle": 25},
            {"std_dev_x": 0.5, "std_dev_y": 0.55, "angle": 30},
        ]
        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []

        def mock_notify_update(key, value):
            updates.append((key, value))

        processor._notify_context_update = mock_notify_update

        # Process the data
        processor._process_logic(
            t_values=t_values,
            gaussian_fit_parameters=gaussian_fit_parameters,
            fitting_model=fitting_model,
        )

        # Verify the results
        assert len(updates) == 1
        assert updates[0][0] == "std_dev_coefficients"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]

    def test_multi_level_nested_path(self):
        """Test nested path with multiple levels."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="time",
            dependent_var_key="data.measurements.values",
            context_keyword="output",
        )

        processor = processor_cls()

        time = [1, 2, 3]
        data = [
            {"measurements": {"values": 1.0, "errors": 0.1}},
            {"measurements": {"values": 2.0, "errors": 0.2}},
            {"measurements": {"values": 3.0, "errors": 0.3}},
        ]
        fitting_model = PolynomialFittingModel(degree=1)

        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        processor._process_logic(time=time, data=data, fitting_model=fitting_model)

        assert len(updates) == 1
        assert updates[0][0] == "output"

    def test_no_nested_path(self):
        """Test behavior when no nested path is used."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="y_data",
            context_keyword="output",
        )

        processor = processor_cls()

        x_data = [1, 2, 3]
        y_data = [1.1, 2.0, 2.9]
        fitting_model = PolynomialFittingModel(degree=1)

        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        processor._process_logic(
            x_data=x_data, y_data=y_data, fitting_model=fitting_model
        )

        assert len(updates) == 1
        assert updates[0][0] == "output"


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    def test_missing_independent_variable(self):
        """Test error when independent variable is missing."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="y_data",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(ValueError, match="Missing required parameter: x_data"):
            processor._process_logic(
                y_data=[1, 2, 3], fitting_model=PolynomialFittingModel(degree=1)
            )

    def test_missing_dependent_variable(self):
        """Test error when dependent variable is missing."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="y_data",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(ValueError, match="Missing required parameter: y_data"):
            processor._process_logic(
                x_data=[1, 2, 3], fitting_model=PolynomialFittingModel(degree=1)
            )

    def test_missing_fitting_model(self):
        """Test error when fitting model is missing."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="y_data",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(
            ValueError, match="Missing required parameter: fitting_model"
        ):
            processor._process_logic(x_data=[1, 2, 3], y_data=[1, 2, 3])

    def test_invalid_nested_path_in_dictionary(self):
        """Test error when nested path doesn't exist in dictionary."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="nested.missing_key",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(
            KeyError, match="Cannot access path 'missing_key' in nested"
        ):
            processor._process_logic(
                x_data=[1, 2, 3],
                nested={"existing_key": [1, 2, 3]},
                fitting_model=PolynomialFittingModel(degree=1),
            )

    def test_invalid_nested_path_in_list(self):
        """Test error when nested path doesn't exist in list of dictionaries."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="data.missing_key",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(KeyError, match="Cannot access path 'missing_key' in item"):
            processor._process_logic(
                x_data=[1, 2, 3],
                data=[{"existing_key": 1}, {"existing_key": 2}, {"existing_key": 3}],
                fitting_model=PolynomialFittingModel(degree=1),
            )

    def test_invalid_list_contents(self):
        """Test error when list contains non-dictionaries."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="data.value",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(ValueError, match="Expected list of dictionaries for data"):
            processor._process_logic(
                x_data=[1, 2, 3],
                data=[1, 2, 3],  # List of numbers, not dictionaries
                fitting_model=PolynomialFittingModel(degree=1),
            )

    def test_invalid_data_type_for_nested_path(self):
        """Test error when data type is neither dict nor list for nested path."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="x_data",
            dependent_var_key="data.value",
            context_keyword="output",
        )

        processor = processor_cls()

        with pytest.raises(
            ValueError, match="Expected dictionary or list of dictionaries"
        ):
            processor._process_logic(
                x_data=[1, 2, 3],
                data="not_a_dict_or_list",
                fitting_model=PolynomialFittingModel(degree=1),
            )


class TestPipelineIntegration:
    """Test suite for pipeline integration functionality."""

    def test_pipeline_node_factory_integration(self):
        """Test that the pipeline node factory correctly handles the configuration."""
        # Initialize registry
        ClassRegistry.initialize_default_modules()

        # Pipeline configuration like in the client's example
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.std_dev_x",
                "context_keyword": "std_dev_coefficients",
            },
        }

        # Create the node
        node = _pipeline_node_factory(node_definition)

        # Verify the processor was created correctly
        processor_cls = type(node.processor)
        expected_params = ["t_values", "gaussian_fit_parameters", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params
        assert processor_cls.get_created_keys() == ["std_dev_coefficients"]

    def test_multiple_fitting_nodes(self):
        """Test creating multiple fitting nodes with different parameters."""
        ClassRegistry.initialize_default_modules()

        # First node configuration
        node_def1 = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.std_dev_x",
                "context_keyword": "std_dev_coefficients",
            },
        }

        # Second node configuration
        node_def2 = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.angle",
                "context_keyword": "orientation_coefficients",
            },
        }

        # Create both nodes
        node1 = _pipeline_node_factory(node_def1)
        node2 = _pipeline_node_factory(node_def2)

        # Verify first node
        processor_cls1 = type(node1.processor)
        assert processor_cls1.get_processing_parameter_names() == [
            "t_values",
            "gaussian_fit_parameters",
            "fitting_model",
        ]
        assert processor_cls1.get_created_keys() == ["std_dev_coefficients"]

        # Verify second node
        processor_cls2 = type(node2.processor)
        assert processor_cls2.get_processing_parameter_names() == [
            "t_values",
            "gaussian_fit_parameters",
            "fitting_model",
        ]
        assert processor_cls2.get_created_keys() == ["orientation_coefficients"]

    def test_fallback_to_standard_processor(self):
        """Test that standard ModelFittingContextProcessor is used when no mapping parameters."""
        ClassRegistry.initialize_default_modules()

        # Standard configuration without mapping parameters
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "context_keyword": "fit_results",
            },
        }

        # Create the node
        node = _pipeline_node_factory(node_definition)

        # Should use standard ModelFittingContextProcessor
        processor_cls = type(node.processor)
        assert processor_cls.get_created_keys() == ["fit_results"]

        # Should expect standard parameters
        import inspect

        sig = inspect.signature(processor_cls._process_logic)
        params = list(sig.parameters.keys())
        assert "x_values" in params
        assert "y_values" in params

    def test_context_keyword_only_configuration(self):
        """Test configuration with only context_keyword (no variable mapping)."""
        ClassRegistry.initialize_default_modules()

        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "context_keyword": "custom_output",
            },
        }

        node = _pipeline_node_factory(node_definition)
        processor_cls = type(node.processor)

        # Should use the with_context_keyword factory method
        assert processor_cls.get_created_keys() == ["custom_output"]
        assert processor_cls.CONTEXT_OUTPUT_KEY == "custom_output"


class TestDocumentationExamples:
    """Test suite to verify all documentation examples work correctly."""

    def test_basic_usage_configuration(self):
        """Test the basic usage configuration from documentation."""
        ClassRegistry.initialize_default_modules()

        # Basic Usage example from docs
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=2",
                "context_keyword": "polynomial_fit",
            },
        }

        node = _pipeline_node_factory(node_definition)
        processor_cls = type(node.processor)

        # Verify this uses standard processor with custom output key
        assert processor_cls.get_created_keys() == ["polynomial_fit"]
        assert processor_cls.CONTEXT_OUTPUT_KEY == "polynomial_fit"

    def test_custom_parameter_names_configuration(self):
        """Test the custom parameter names configuration from documentation."""
        ClassRegistry.initialize_default_modules()

        # Custom Parameter Names example from docs
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "time_values",
                "dependent_var_key": "measurements",
                "context_keyword": "time_series_fit",
            },
        }

        node = _pipeline_node_factory(node_definition)
        processor_cls = type(node.processor)

        # Should use factory-created processor
        expected_params = ["time_values", "measurements", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params
        assert processor_cls.get_created_keys() == ["time_series_fit"]

    def test_nested_path_extraction_configuration(self):
        """Test the nested path extraction configuration from documentation."""
        ClassRegistry.initialize_default_modules()

        # Nested Path Extraction example from docs
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.std_dev_x",
                "context_keyword": "std_dev_coefficients",
            },
        }

        node = _pipeline_node_factory(node_definition)
        processor_cls = type(node.processor)

        # Should use factory-created processor with nested path support
        expected_params = ["t_values", "gaussian_fit_parameters", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params
        assert processor_cls.get_created_keys() == ["std_dev_coefficients"]

    def test_single_dictionary_format_from_docs(self):
        """Test the exact single dictionary format from documentation."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="test_output",
        )

        processor = processor_cls()

        # Exact data structure from documentation
        data = {
            "t_values": [1.0, 2.0, 3.0, 4.0, 5.0],
            "gaussian_fit_parameters": {
                "std_dev_x": [0.1, 0.2, 0.3, 0.4, 0.5],
                "std_dev_y": [0.15, 0.25, 0.35, 0.45, 0.55],
                "angle": [10, 15, 20, 25, 30],
            },
        }

        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        # Process the exact data structure from docs
        processor._process_logic(
            t_values=data["t_values"],
            gaussian_fit_parameters=data["gaussian_fit_parameters"],
            fitting_model=fitting_model,
        )

        # Verify processing worked
        assert len(updates) == 1
        assert updates[0][0] == "test_output"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]

    def test_list_of_dictionaries_format_from_docs(self):
        """Test the exact list of dictionaries format from documentation."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="test_output",
        )

        processor = processor_cls()

        # Exact data structure from documentation (Slicer Output)
        data = {
            "t_values": [1.0, 2.0, 3.0, 4.0, 5.0],
            "gaussian_fit_parameters": [
                {"std_dev_x": 0.1, "std_dev_y": 0.15, "angle": 10},
                {"std_dev_x": 0.2, "std_dev_y": 0.25, "angle": 15},
                {"std_dev_x": 0.3, "std_dev_y": 0.35, "angle": 20},
                {"std_dev_x": 0.4, "std_dev_y": 0.45, "angle": 25},
                {"std_dev_x": 0.5, "std_dev_y": 0.55, "angle": 30},
            ],
        }

        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        # Process the exact data structure from docs
        processor._process_logic(
            t_values=data["t_values"],
            gaussian_fit_parameters=data["gaussian_fit_parameters"],
            fitting_model=fitting_model,
        )

        # Verify processing worked
        assert len(updates) == 1
        assert updates[0][0] == "test_output"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]

    def test_slicer_integration_configuration(self):
        """Test the slicer integration configuration from documentation."""
        ClassRegistry.initialize_default_modules()

        # Slicer Integration example from docs
        node_definition = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "slice_indices",
                "dependent_var_key": "aggregated_data.mean_values",
                "context_keyword": "trend_analysis",
            },
        }

        node = _pipeline_node_factory(node_definition)
        processor_cls = type(node.processor)

        # Should use factory-created processor
        expected_params = ["slice_indices", "aggregated_data", "fitting_model"]
        assert processor_cls.get_processing_parameter_names() == expected_params
        assert processor_cls.get_created_keys() == ["trend_analysis"]

    def test_slicer_integration_data_processing(self):
        """Test actual data processing for slicer integration scenario."""
        processor_cls = _model_fitting_processor_factory(
            independent_var_key="slice_indices",
            dependent_var_key="aggregated_data.mean_values",
            context_keyword="trend_analysis",
        )

        processor = processor_cls()

        # Simulated slicer output data
        slice_indices = [0, 1, 2, 3, 4]
        aggregated_data = {
            "mean_values": [2.1, 4.0, 5.9, 8.1, 9.8],
            "std_values": [0.2, 0.3, 0.4, 0.3, 0.2],
            "count": [10, 12, 8, 11, 9],
        }

        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        # Process the slicer integration data
        processor._process_logic(
            slice_indices=slice_indices,
            aggregated_data=aggregated_data,
            fitting_model=fitting_model,
        )

        # Verify processing worked
        assert len(updates) == 1
        assert updates[0][0] == "trend_analysis"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]

    def test_multiple_fitting_operations_scenario(self):
        """Test multiple fitting operations on the same data as shown in documentation."""
        ClassRegistry.initialize_default_modules()

        # Create two different fitting processors as shown in docs
        std_dev_node_def = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.std_dev_x",
                "context_keyword": "std_dev_trend",
            },
        }

        orientation_node_def = {
            "processor": "ModelFittingContextProcessor",
            "parameters": {
                "fitting_model": "model:PolynomialFittingModel:degree=1",
                "independent_var_key": "t_values",
                "dependent_var_key": "gaussian_fit_parameters.angle",
                "context_keyword": "orientation_trend",
            },
        }

        # Create both nodes
        std_dev_node = _pipeline_node_factory(std_dev_node_def)
        orientation_node = _pipeline_node_factory(orientation_node_def)

        # Verify both processors were created correctly
        std_dev_cls = type(std_dev_node.processor)
        orientation_cls = type(orientation_node.processor)

        assert std_dev_cls.get_created_keys() == ["std_dev_trend"]
        assert orientation_cls.get_created_keys() == ["orientation_trend"]

        # Both should expect the same base parameter
        expected_params = ["t_values", "gaussian_fit_parameters", "fitting_model"]
        assert std_dev_cls.get_processing_parameter_names() == expected_params
        assert orientation_cls.get_processing_parameter_names() == expected_params

    def test_multiple_fitting_operations_data_processing(self):
        """Test actual data processing for multiple fitting operations."""
        # Create processors for both std_dev and angle fitting
        std_dev_processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.std_dev_x",
            context_keyword="std_dev_trend",
        )

        orientation_processor_cls = _model_fitting_processor_factory(
            independent_var_key="t_values",
            dependent_var_key="gaussian_fit_parameters.angle",
            context_keyword="orientation_trend",
        )

        std_dev_processor = std_dev_processor_cls()
        orientation_processor = orientation_processor_cls()

        # Shared data structure
        t_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        gaussian_fit_parameters = [
            {"std_dev_x": 0.1, "std_dev_y": 0.15, "angle": 10},
            {"std_dev_x": 0.2, "std_dev_y": 0.25, "angle": 15},
            {"std_dev_x": 0.3, "std_dev_y": 0.35, "angle": 20},
            {"std_dev_x": 0.4, "std_dev_y": 0.45, "angle": 25},
            {"std_dev_x": 0.5, "std_dev_y": 0.55, "angle": 30},
        ]

        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates for both processors
        std_dev_updates = []
        orientation_updates = []

        std_dev_processor._notify_context_update = lambda k, v: std_dev_updates.append(
            (k, v)
        )
        orientation_processor._notify_context_update = (
            lambda k, v: orientation_updates.append((k, v))
        )

        # Process with both processors (simulating pipeline execution)
        std_dev_processor._process_logic(
            t_values=t_values,
            gaussian_fit_parameters=gaussian_fit_parameters,
            fitting_model=fitting_model,
        )

        orientation_processor._process_logic(
            t_values=t_values,
            gaussian_fit_parameters=gaussian_fit_parameters,
            fitting_model=fitting_model,
        )

        # Verify both processors worked correctly
        assert len(std_dev_updates) == 1
        assert std_dev_updates[0][0] == "std_dev_trend"
        assert "coeff_0" in std_dev_updates[0][1]
        assert "coeff_1" in std_dev_updates[0][1]

        assert len(orientation_updates) == 1
        assert orientation_updates[0][0] == "orientation_trend"
        assert "coeff_0" in orientation_updates[0][1]
        assert "coeff_1" in orientation_updates[0][1]


class TestBackwardCompatibility:
    """Test suite to ensure backward compatibility."""

    def test_original_processor_unchanged(self):
        """Test that original ModelFittingContextProcessor is unchanged."""
        # Test original class functionality
        processor = ModelFittingContextProcessor()

        # Check default output key
        assert processor.CONTEXT_OUTPUT_KEY == "fit.parameters"
        assert processor.context_keys() == ["fit.parameters"]

        # Check signature hasn't changed
        import inspect

        sig = inspect.signature(processor._process_logic)
        params = list(sig.parameters.keys())

        assert "x_values" in params
        assert "y_values" in params
        assert "fitting_model" in params

    def test_with_context_keyword_still_works(self):
        """Test that the existing with_context_keyword method still works."""
        processor_cls = ModelFittingContextProcessor.with_context_keyword(
            "custom_output"
        )

        assert processor_cls.CONTEXT_OUTPUT_KEY == "custom_output"
        assert processor_cls.get_created_keys() == ["custom_output"]
        assert processor_cls.context_keys() == ["custom_output"]

    def test_original_functionality_preserved(self):
        """Test that original fitting functionality is preserved."""
        processor = ModelFittingContextProcessor()

        # Test data
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [1.1, 1.9, 3.1, 3.9, 5.1]
        fitting_model = PolynomialFittingModel(degree=1)

        # Track context updates
        updates = []
        processor._notify_context_update = lambda k, v: updates.append((k, v))

        # Process using original interface
        processor._process_logic(
            x_values=x_values, y_values=y_values, fitting_model=fitting_model
        )

        # Verify results
        assert len(updates) == 1
        assert updates[0][0] == "fit.parameters"
        assert "coeff_0" in updates[0][1]
        assert "coeff_1" in updates[0][1]
