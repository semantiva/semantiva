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

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union

import numpy as np

from semantiva.context_processors.context_processors import ContextProcessor
from semantiva.context_processors.context_types import ContextType
from semantiva.logger import Logger

X = TypeVar("X")  # Domain (annotation) type (e.g., float, tuple[int, float], etc.)
Y = TypeVar("Y")  # Codomain (extracted features) type (e.g., float, list, dict, etc.)


class FittingModel(ABC, Generic[X, Y]):
    """
    Abstract base class for function-fitting models.

    This class defines an interface for fitting a mathematical model to data.
    Subclasses must implement the `fit` method, which computes optimal parameters
    based on observed features.

    The fitting model takes annotation values (domain) and extracted features (codomain)
    and returns estimated parameters.

    Type Parameters:
        X: The domain type (annotation values such as lens positions).
        Y: The codomain type (extracted features such as image sharpness).

    Methods:
        fit(x_values: List[X], y_values: List[Y]) -> Dict[str, float]:
            Fits a function to data and returns estimated parameters.
    """

    def __str__(self) -> str:
        """
        Returns the class name of the fitting model.

        Returns:
            str: The class name.
        """
        return self.__class__.__name__

    @abstractmethod
    def fit(self, x_values: List[X], y_values: List[Y]) -> Dict[str, float]:
        """
        Fits a function to data and returns estimated parameters.

        Args:
            x_values (List[X]): The annotation values (domain, e.g., lens positions).
            y_values (List[Y]): The extracted features (codomain, e.g., sharpness scores).

        Returns:
            Dict[str, float]: A dictionary of best-fit parameters.
        """
        pass


class PolynomialFittingModel(FittingModel[float, float]):
    """
    Polynomial fitting model using least squares regression.

    This model fits a polynomial function to a given dataset and returns
    the estimated coefficients as a dictionary.
    """

    def __init__(self, degree: int):
        """
        Initializes the polynomial fitting model.

        Args:
            degree (int): The degree of the polynomial to be fitted.
        """
        self.degree = degree

    def fit(self, x_values: List[float], y_values: List[float]) -> Dict[str, float]:
        """
        Fits a polynomial function to data and returns estimated parameters.

        Ensures type consistency by converting NumPy float64 values to Python floats.

        Args:
            x_values (List[float]): The annotation values (domain, e.g., lens positions).
            y_values (List[float]): The extracted features (codomain, e.g., sharpness scores).

        Returns:
            Dict[str, float]: A dictionary containing polynomial coefficients.
        """
        coefficients = np.polyfit(x_values, y_values, self.degree)
        return {
            f"coeff_{i}": float(coeff) for i, coeff in enumerate(reversed(coefficients))
        }  # Explicit cast

    def __str__(self) -> str:
        """
        Returns the class name of the fitting model along with the polynomial degree.

        Returns:
            str: The class name and polynomial degree.
        """
        return f"{self.__class__.__name__}(degree={self.degree})"


class ModelFittingContextProcessor(ContextProcessor):
    """ContextProcessor that fits extracted features using a specified model."""

    def __init__(
        self,
        logger: Optional[Logger],
        fitting_model: FittingModel,
        independent_var_key: str,
        dependent_var_key: Union[str, Tuple[str, str], List[str]],
        context_keyword: str,
    ) -> None:
        super().__init__(logger)
        self.logger.debug(f"Initializing {self.__class__.__name__}")
        self.fitting_model: FittingModel = fitting_model
        self.independent_var_key = independent_var_key
        self.context_keyword = context_keyword

        if isinstance(dependent_var_key, (tuple, list)):
            self.dependent_var_key = dependent_var_key[0]
            self.dependent_var_subkey: Optional[str] = dependent_var_key[1]
        else:
            self.dependent_var_key = dependent_var_key
            self.dependent_var_subkey = None

        if not isinstance(independent_var_key, str):
            raise TypeError(
                f"independent_var_key must be a string, got {type(independent_var_key).__name__} with value {independent_var_key}"
            )

    def _process_logic(self, context: ContextType) -> ContextType:
        """Fit extracted features to the model using context data."""

        # Retrieve independent and dependent variables from context
        independent_variable = context.get_value(self.independent_var_key)
        dependent_variable = context.get_value(self.dependent_var_key)

        # Ensure required parameters exist
        if independent_variable is None or dependent_variable is None:
            missing_params = [
                p for p in self.get_required_keys() if context.get_value(p) is None
            ]
            raise ValueError(
                f"Missing required context parameters: {', '.join(str(missing_params))}"
            )

        # Extract dependent_variable from dictionary if needed
        if isinstance(self.dependent_var_subkey, tuple):
            dependent_variable_ = tuple(
                dependent_variable[key] for key in self.dependent_var_subkey
            )
        elif isinstance(self.dependent_var_subkey, str):
            dependent_variable_ = [
                item[self.dependent_var_subkey] for item in dependent_variable
            ]
        elif isinstance(dependent_variable, list):
            dependent_variable_ = dependent_variable
        else:
            raise ValueError("Invalid type for dependent_variable")

        # Fit the model using extracted features
        self.logger.debug("\tRunning model %s", self.fitting_model)
        self.logger.debug(f"\t\tindependent_variable = {independent_variable}")
        self.logger.debug(f"\t\tdependent_variable = {dependent_variable_}")
        fit_results = self.fitting_model.fit(independent_variable, dependent_variable_)

        # Store the results back in context under the dependent variable name
        context.set_value(self.context_keyword, fit_results)

        return context

    def get_required_keys(self) -> List[str]:
        """Retrieve the list of required keys for the context operation."""
        return [self.independent_var_key, self.dependent_var_key]

    def get_created_keys(self) -> List[str]:
        """Retrieves the list of keys created in the context."""
        return [self.context_keyword]

    def get_suppressed_keys(self) -> List[str]:
        """This operation does not suppress any keys."""
        return []


# Example Usage:
if __name__ == "__main__":
    # Generate sample data
    x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_data = [2.2, 2.8, 3.6, 4.5, 5.1]

    model = PolynomialFittingModel(degree=2)
    parameters = model.fit(x_data, y_data)
    print(parameters)
