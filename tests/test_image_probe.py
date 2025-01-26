import pytest
import numpy as np
from scipy.stats import multivariate_normal
from semantiva.specializations.image.image_data_types import ImageDataType
from semantiva.specializations.image.image_probes import (
    BasicImageProbe,
    TwoDGaussianFitterProbe,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
)


@pytest.fixture
def basic_probe():
    return BasicImageProbe()


@pytest.fixture
def gaussian_fitter_probe():
    return TwoDGaussianFitterProbe()


@pytest.fixture
def gaussian_image_generator():
    return TwoDGaussianImageGenerator()


def test_basic_image_probe(basic_probe, gaussian_image_generator):
    # Create a test image
    std_dev_x, std_dev_y, amplitude, image_size = 1.0, 2.0, 5.0, (50, 50)
    test_image = gaussian_image_generator.get_data(
        std_dev_x, std_dev_y, amplitude, image_size
    )
    # Compute statistics using the probe
    stats = basic_probe.process(test_image)

    # Assert that statistics are calculated correctly
    assert "mean" in stats
    assert "sum" in stats
    assert "min" in stats
    assert "max" in stats
    assert stats["min"] >= 0


def test_two_d_gaussian_fitter_probe(gaussian_fitter_probe, gaussian_image_generator):
    # Generate a test image
    std_dev_x, std_dev_y, amplitude, image_size = 1.0, 2.0, 5.0, (50, 50)
    test_image = gaussian_image_generator.get_data(
        std_dev_x, std_dev_y, amplitude, image_size
    )

    # Fit the Gaussian
    initial_guess = [amplitude, 0, 0, std_dev_x, std_dev_y]
    result = gaussian_fitter_probe.process(test_image)

    # Assert the fit parameters and R-squared value
    assert "peak_center" in result
    assert "amplitude" in result
    assert "std_dev_x" in result
    assert "std_dev_y" in result
    assert "r_squared" in result
    assert result["r_squared"] > 0.9  # Ensure a good fit


def test_two_d_gaussian_image_generator(gaussian_image_generator):
    # Define parameters for the test Gaussian image
    std_dev_x, std_dev_y, amplitude, image_size = 1.0, 2.0, 5.0, (50, 50)

    # Generate the image
    generated_image = gaussian_image_generator.get_data(
        std_dev_x, std_dev_y, amplitude, image_size
    )

    # Assert that the generated image has the correct dimensions
    assert generated_image.data.shape == image_size

    # Assert that the image contains positive values
    assert np.all(generated_image.data >= 0)

    # Assert that the maximum value matches the amplitude (approximately)
    print(generated_image.data.max())
    assert np.isclose(generated_image.data.max(), amplitude, atol=0.1)
