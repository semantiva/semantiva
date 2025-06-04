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
from typing import TypeVar, Generic, List, Dict

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


import numpy as np
from typing import List, Dict


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


# Example Usage:
if __name__ == "__main__":
    # Generate sample data
    x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_data = [2.2, 2.8, 3.6, 4.5, 5.1]

    model = PolynomialFittingModel(degree=2)
    parameters = model.fit(x_data, y_data)
    print(parameters)
