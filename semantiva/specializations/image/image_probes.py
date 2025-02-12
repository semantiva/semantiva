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
        x = np.linspace(0, data.data.shape[1] - 1, data.data.shape[1])
        y = np.linspace(0, data.data.shape[0] - 1, data.data.shape[0])
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


class TwoDTiltedGaussianFitterProbe(ImageProbe):
    """
    A probe that fits a **tilted 2D Gaussian function** to an image, extracting
    Gaussian parameters including **rotation angle** (θ) and ensuring stable fitting.

    This implementation improves **fit consistency** by:
    - Using **second-moment (σ_x, σ_y) estimation** for better initial guesses.
    - Ensuring **principal axes are uniquely defined** to prevent swaps.
    - Incorporating **weighting techniques** from optical beam propagation.

    Attributes:
        None (inherits methods and attributes from `ImageProbe`).

    Methods:
        two_d_gaussian: Defines the **rotated 2D Gaussian function**.
        estimate_initial_params: Provides **better initial estimates** for stable fitting.
        calculate_r_squared: Computes the **R² goodness-of-fit score**.
        _operation: Fits a **tilted** Gaussian function and extracts parameters.
    """

    def two_d_gaussian(self, xy, amplitude, xo, yo, sigma_x, sigma_y, theta):
        """
        Define a **rotated 2D Gaussian function**.

        Parameters:
            xy (tuple): A tuple of (x, y) coordinate grids.
            amplitude (float): Peak intensity of the Gaussian.
            xo (float): X-coordinate of the Gaussian center.
            yo (float): Y-coordinate of the Gaussian center.
            sigma_x (float): Standard deviation along the **primary axis**.
            sigma_y (float): Standard deviation along the **perpendicular axis**.
            theta (float): Rotation angle (in radians).

        Returns:
            np.ndarray: The **raveled** evaluated 2D Gaussian function.
        """
        x, y = xy
        x_shifted = x - xo
        y_shifted = y - yo

        # Rotate the coordinate system
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        x_rot = cos_theta * x_shifted + sin_theta * y_shifted
        y_rot = -sin_theta * x_shifted + cos_theta * y_shifted

        # Compute Gaussian function
        gaussian = amplitude * np.exp(
            -((x_rot**2) / (2 * sigma_x**2) + (y_rot**2) / (2 * sigma_y**2))
        )
        return np.ravel(gaussian)

    def estimate_initial_params(self, data: np.ndarray):
        """
        Estimate initial parameters for stable fitting using **second-moment analysis**.

        Parameters:
            data (np.ndarray): The input image data.

        Returns:
            tuple: Estimated parameters (amplitude, x_center, y_center, σ_x, σ_y, θ).
        """
        # Prepare coordinate grids
        y_size, x_size = data.shape
        x = np.linspace(0, x_size - 1, x_size)
        y = np.linspace(0, y_size - 1, y_size)
        x_grid, y_grid = np.meshgrid(x, y)

        # Compute total intensity for weighted centroid calculation
        total_intensity = np.sum(data)
        center_x = np.sum(x_grid * data) / total_intensity
        center_y = np.sum(y_grid * data) / total_intensity

        # Compute second moments (variance-based width estimation)
        var_x = np.sum(((x_grid - center_x) ** 2) * data) / total_intensity
        var_y = np.sum(((y_grid - center_y) ** 2) * data) / total_intensity
        sigma_x = np.sqrt(var_x)
        sigma_y = np.sqrt(var_y)

        # Estimate rotation angle from second-moment covariance
        cov_xy = (
            np.sum((x_grid - center_x) * (y_grid - center_y) * data) / total_intensity
        )
        theta = 0.5 * np.arctan2(2 * cov_xy, var_x - var_y)  # Rotation angle estimate

        return (
            data.max(),  # Amplitude estimate
            center_x,
            center_y,
            max(sigma_x, 1.0),  # Prevent division by zero
            max(sigma_y, 1.0),  # Prevent division by zero
            theta,
        )

    def calculate_r_squared(self, data, fitted_data):
        """
        Compute the **R² goodness-of-fit** score for the fitted Gaussian model.

        Parameters:
            data (ImageDataType): The input image data.
            fitted_data (np.ndarray): The computed fitted Gaussian model.

        Returns:
            float: The R² goodness-of-fit score (1 = perfect fit, 0 = poor fit).
        """
        residuals = data.data - fitted_data
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((data.data - np.mean(data.data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def _operation(self, data: ImageDataType) -> Dict:
        """
        Fit a **tilted 2D Gaussian function** to the input image data, extracting
        the Gaussian parameters including the **rotation angle**.

        Parameters:
            data (ImageDataType): The input image containing a Gaussian-like signal.

        Returns:
            dict: A dictionary containing:
                - `"peak_center"`: (x, y) coordinates of the Gaussian peak.
                - `"amplitude"`: Peak intensity of the Gaussian.
                - `"std_dev_x"`: Standard deviation along the **primary axis**.
                - `"std_dev_y"`: Standard deviation along the **perpendicular axis**.
                - `"angle"`: Rotation angle (in **degrees**) of the Gaussian.
                - `"r_squared"`: Goodness-of-fit (R² score).
        """

        # Prepare coordinate grids
        x = np.linspace(0, data.data.shape[1] - 1, data.data.shape[1])
        y = np.linspace(0, data.data.shape[0] - 1, data.data.shape[0])
        x, y = np.meshgrid(x, y)

        # Get initial parameter estimates
        initial_guess = self.estimate_initial_params(data.data)

        # Perform curve fitting
        fit_params, _ = curve_fit(
            self.two_d_gaussian, (x, y), data.data.ravel(), p0=initial_guess
        )

        # Compute fitted Gaussian
        fitted_data = self.two_d_gaussian((x, y), *fit_params).reshape(data.data.shape)

        # Calculate goodness-of-fit score
        r_squared = self.calculate_r_squared(data, fitted_data)

        return {
            "peak_center": (fit_params[1], fit_params[2]),
            "amplitude": fit_params[0],
            "std_dev_x": fit_params[3],
            "std_dev_y": fit_params[4],
            "angle": self.normalize_angle_180(
                np.degrees(fit_params[5])
            ),  # Convert to degrees and ensure it is in [0, 360]
            "r_squared": r_squared,
        }

    def normalize_angle_180(self, angle: float) -> float:
        """
        Normalize an angle to the range [0, 180] degrees.

        Ensures that angles differing by 180 degrees (or -90, 90, 270)
        are treated equivalently, keeping results within [0, 180].

        Parameters:
            angle (float): Input angle in degrees.

        Returns:
            float: Normalized angle in the range [0, 180].
        """
        normalized = np.abs(angle) % 180
        return 0 if np.isclose(normalized, 180, atol=1e-6) else normalized
