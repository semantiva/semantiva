from scipy.optimize import curve_fit
import numpy as np
from typing import Dict
from semantiva.specializations.image.image_operations import ImageProbe
from semantiva.specializations.image.image_data_types import ImageDataType


class BasicImageProbe(ImageProbe):
    """
    A basic image probe that computes essential image statistics.

    This class provides a simple probe to calculate key statistical properties of an image,
    such as mean, sum, minimum value, and maximum value.
    """

    def _operation(self, data):
        """
        Compute essential image statistics.

        Args:
            data (ImageDataType): The input image data.

        Returns:
            dict: A dictionary of image statistics.
        """
        return {
            "mean": data.data.mean(),
            "sum": data.data.sum(),
            "min": data.data.min(),
            "max": data.data.max(),
        }


class TwoDGaussianFitterProbe(ImageProbe):
    """
    A probe that fits a 2D Gaussian function to an image and computes the goodness-of-fit score.

    This class provides functionality to fit a 2D Gaussian function to image data and returns
    the fit parameters along with the goodness-of-fit score (R²).
    """

    def two_d_gaussian(self, xy, amplitude, xo, yo, sigma_x, sigma_y):
        """
        Define a 2D Gaussian function.

        Parameters:
            xy (tuple): A tuple of (x, y) coordinates.
            amplitude (float): The amplitude of the Gaussian.
            xo (float): The x-coordinate of the Gaussian center.
            yo (float): The y-coordinate of the Gaussian center.
            sigma_x (float): The standard deviation along the x-axis.
            sigma_y (float): The standard deviation along the y-axis.

        Returns:
            np.ndarray: The evaluated 2D Gaussian function as a raveled array.
        """
        x, y = xy
        two_d_gaussian = amplitude * np.exp(
            -((x - xo) ** 2) / (2 * sigma_x**2) - (y - yo) ** 2 / (2 * sigma_y**2)
        )
        return np.ravel(two_d_gaussian)

    def calculate_r_squared(self, data, fitted_data):
        """
        Calculate the R² goodness-of-fit score for a 2D Gaussian fit.

        Parameters:
            data (ImageDataType): The input image data.
            fit_params (tuple): The optimized parameters of the Gaussian function.

        Returns:
            float: The R² goodness-of-fit score.
        """
        residuals = data.data - fitted_data
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((data.data - np.mean(data.data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def _operation(self, data: ImageDataType) -> Dict:
        """
        Fit a 2D Gaussian function to the input image data and compute the goodness-of-fit score.

        Parameters:
            data (ImageDataType): The input image data.

        Returns:
            dict: A dictionary containing:
                - "fit_params": The optimized parameters of the Gaussian function.
                - "r_squared": The R² goodness-of-fit score.
        """

        # Prepare the x and y coordinate grids
        x = np.linspace(0, data.data.shape[1], data.data.shape[1])
        y = np.linspace(0, data.data.shape[0], data.data.shape[0])
        x, y = np.meshgrid(x, y)

        # Perform the curve fitting
        # Compute the center of mass as a better initial guess
        total_intensity = np.sum(data.data)
        center_x = np.sum(x * data.data) / total_intensity
        center_y = np.sum(y * data.data) / total_intensity

        initial_guess = [
            data.data.max(),
            center_x,  # Use the center of mass
            center_y,  # Use the center of mass
            1,
            1,
        ]
        fit_params = curve_fit(
            self.two_d_gaussian, (x, y), data.data.ravel(), p0=initial_guess
        )
        # Calculate the R² goodness-of-fit score
        fitted_data = self.two_d_gaussian((x, y), *fit_params[0]).reshape(
            data.data.shape
        )
        r_squared = self.calculate_r_squared(data, fitted_data)

        return {
            "peak_center": (fit_params[0][1], fit_params[0][2]),
            "amplitude": fit_params[0][0],
            "std_dev_x": fit_params[0][3],
            "std_dev_y": fit_params[0][4],
            "r_squared": r_squared,
        }
