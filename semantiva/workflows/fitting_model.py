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

"""Model fitting workflow components for Semantiva pipelines.

Provides FittingModel interface, PolynomialFittingModel implementation, and
ModelFittingContextProcessor with flexible parameter mapping support.

See documentation: workflows_fitting_models.rst
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, TypeVar

import numpy as np

from semantiva.context_processors.context_processors import ContextProcessor

X = TypeVar("X")  # Domain (annotation) type (e.g., float, tuple[int, float], etc.)
Y = TypeVar("Y")  # Codomain (extracted features) type (e.g., float, list, dict, etc.)


class FittingModel(ABC, Generic[X, Y]):
    """Abstract base class for function-fitting models."""

    def __str__(self) -> str:
        """
        Returns the class name of the fitting model.

        Returns:
            str: The class name.
        """
        return self.__class__.__name__

    @abstractmethod
    def fit(self, x_values: List[X], y_values: List[Y]) -> Dict[str, float]:
        """Fit model to data and return estimated parameters."""
        pass


class PolynomialFittingModel(FittingModel[float, float]):
    """Polynomial fitting model using least squares regression."""

    def __init__(self, degree: int):
        """Initialize polynomial fitting model with specified degree."""
        self.degree = degree

    def fit(self, x_values: List[float], y_values: List[float]) -> Dict[str, float]:
        """Fit polynomial to data and return coefficients."""
        coefficients = np.polyfit(x_values, y_values, self.degree)
        return {
            f"coeff_{i}": float(coeff) for i, coeff in enumerate(reversed(coefficients))
        }  # Explicit cast

    def __str__(self) -> str:
        """Return string representation with degree."""
        return f"{self.__class__.__name__}(degree={self.degree})"


class ModelFittingContextProcessor(ContextProcessor):
    """Context processor that fits mathematical models to x/y data and stores results."""

    CONTEXT_OUTPUT_KEY: str = "fit.parameters"

    @classmethod
    def with_context_keyword(cls, key: str) -> type["ModelFittingContextProcessor"]:
        """Return a subclass with :data:`CONTEXT_OUTPUT_KEY` bound to ``key``."""
        safe = key.replace(".", "_").replace("[", "_").replace("]", "_")
        name = f"{cls.__name__}_OUT_{safe}"
        attrs = {
            "CONTEXT_OUTPUT_KEY": key,
            "__doc__": (cls.__doc__ or "") + f"\n\nBound output key: '{key}'.",
            "context_keys": classmethod(lambda kls: [kls.CONTEXT_OUTPUT_KEY]),
        }
        return type(name, (cls,), attrs)

    def _process_logic(
        self,
        *,
        x_values: List[float],
        y_values: List[float],
        fitting_model: "FittingModel",
    ) -> None:
        if x_values is None or y_values is None:
            raise ValueError("Missing x_values or y_values for model fitting.")
        fit_results = fitting_model.fit(x_values, y_values)
        self._notify_context_update(self.__class__.CONTEXT_OUTPUT_KEY, fit_results)

    @classmethod
    def context_keys(cls) -> List[str]:
        return [cls.CONTEXT_OUTPUT_KEY]


def _model_fitting_processor_factory(
    independent_var_key: str,
    dependent_var_key: str,
    context_keyword: str,
) -> type[ModelFittingContextProcessor]:
    """Create ModelFittingContextProcessor with custom parameter mapping.

    Creates specialized processor class for custom parameter names and nested paths.
    Supports both single dictionaries and lists of dictionaries (e.g., from slicers).

    Args:
        independent_var_key: Parameter name for x-axis data
        dependent_var_key: Parameter name/path for y-axis data (supports "nested.path")
        context_keyword: Output key for fit results

    Returns:
        Dynamically created processor subclass with custom parameter mapping
    """
    import inspect  # pylint: disable=import-outside-toplevel

    # Determine output key
    output_key = context_keyword or ModelFittingContextProcessor.CONTEXT_OUTPUT_KEY

    # Parse dependent variable key to separate parameter name from nested path
    if "." in dependent_var_key:
        dependent_param_name = dependent_var_key.split(".")[0]
        dependent_path = dependent_var_key.split(".", 1)[1]
    else:
        dependent_param_name = dependent_var_key
        dependent_path = None

    # Create safe class name
    safe_name = (
        f"{independent_var_key}_{dependent_var_key}".replace(".", "_")
        .replace("[", "_")
        .replace("]", "_")
    )
    class_name = f"ModelFittingContextProcessor_MAPPED_{safe_name}"

    def create_process_logic():
        def _process_logic_mapped(self, **kwargs):
            """Process logic with custom parameter mapping."""
            # Get parameters using the configured names
            x_values = kwargs.get(independent_var_key)
            y_source = kwargs.get(dependent_param_name)
            fitting_model = kwargs.get("fitting_model")

            # Validate required parameters
            if x_values is None:
                raise ValueError(f"Missing required parameter: {independent_var_key}")
            if y_source is None:
                raise ValueError(f"Missing required parameter: {dependent_param_name}")
            if fitting_model is None:
                raise ValueError("Missing required parameter: fitting_model")

            # Extract y_values from nested path if needed
            if dependent_path is not None:
                if isinstance(y_source, list):
                    # Handle list of dictionaries (e.g., from slicer operations)
                    y_values = []
                    for item in y_source:
                        if not isinstance(item, dict):
                            raise ValueError(
                                f"Expected list of dictionaries for {dependent_param_name}, "
                                f"got list containing {type(item)}"
                            )

                        # Navigate the nested path for each item
                        value = item
                        for key in dependent_path.split("."):
                            if isinstance(value, dict) and key in value:
                                value = value[key]
                            else:
                                raise KeyError(
                                    f"Cannot access path '{dependent_path}' in item {item}"
                                )
                        y_values.append(value)

                elif isinstance(y_source, dict):
                    # Handle single dictionary
                    y_values = y_source
                    for key in dependent_path.split("."):
                        if isinstance(y_values, dict) and key in y_values:
                            y_values = y_values[key]
                        else:
                            raise KeyError(
                                f"Cannot access path '{dependent_path}' in {dependent_param_name}"
                            )
                else:
                    raise ValueError(
                        f"Expected dictionary or list of dictionaries for {dependent_param_name}, "
                        f"got {type(y_source)}"
                    )
            else:
                y_values = y_source

            # Perform the model fitting
            fit_results = fitting_model.fit(x_values, y_values)
            self._notify_context_update(
                output_key, fit_results
            )  # pylint: disable=protected-access

        # Create proper signature with the configured parameter names
        params = [
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(
                independent_var_key, inspect.Parameter.POSITIONAL_OR_KEYWORD
            ),
            inspect.Parameter(
                dependent_param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD
            ),
            inspect.Parameter("fitting_model", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ]
        sig = inspect.Signature(params)
        _process_logic_mapped.__signature__ = sig
        _process_logic_mapped.__name__ = "_process_logic"
        return _process_logic_mapped

    # Define class methods
    def get_processing_parameter_names():
        return [independent_var_key, dependent_param_name, "fitting_model"]

    def get_created_keys():
        return [output_key]

    def context_keys():
        return [output_key]

    # Create the specialized class
    attrs = {
        "CONTEXT_OUTPUT_KEY": output_key,
        "_process_logic": create_process_logic(),
        "get_processing_parameter_names": classmethod(
            lambda cls: get_processing_parameter_names()
        ),
        "get_created_keys": classmethod(lambda cls: get_created_keys()),
        "context_keys": classmethod(lambda cls: context_keys()),
        "__doc__": (
            f"ModelFittingContextProcessor with custom parameter mapping:\n"
            f"  x_values from: {independent_var_key}\n"
            f"  y_values from: {dependent_var_key}\n"
            f"  output to: {output_key}"
        ),
    }

    return type(class_name, (ModelFittingContextProcessor,), attrs)


# Example Usage:
if __name__ == "__main__":
    # Generate sample data
    x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_data = [2.2, 2.8, 3.6, 4.5, 5.1]

    model = PolynomialFittingModel(degree=2)
    parameters = model.fit(x_data, y_data)
    print(parameters)
