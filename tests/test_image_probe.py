import pytest
import numpy as np
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
    # Create a test Gaussian image
    center = (25, 25)  # Updated: Using a tuple for center
    std_dev = (1.0, 2.0)  # Updated: std_dev is also a tuple
    amplitude = 5.0
    image_size = (50, 50)

    test_image = gaussian_image_generator.get_data(
        center=center, std_dev=std_dev, amplitude=amplitude, image_size=image_size
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
    # Generate a test Gaussian image
    center = (25, 25)  # Updated: Tuple for center
    std_dev = (1.0, 2.0)  # Updated: Tuple for std_dev
    amplitude = 5.0
    image_size = (50, 50)

    test_image = gaussian_image_generator.get_data(
        center=center, std_dev=std_dev, amplitude=amplitude, image_size=image_size
    )

    # Fit the Gaussian
    result = gaussian_fitter_probe.process(test_image)

    # Assert the fit parameters and R-squared value
    assert "peak_center" in result
    assert "amplitude" in result
    assert "std_dev_x" in result
    assert "std_dev_y" in result
    assert "r_squared" in result
    assert result["r_squared"] > 0.9  # Ensure a good fit

    # Additional check: The detected center should be close to the actual center
    assert np.isclose(result["peak_center"][0], center[0], atol=1)
    assert np.isclose(result["peak_center"][1], center[1], atol=1)


def test_two_d_gaussian_image_generator(gaussian_image_generator):
    # Define parameters for the test Gaussian image
    center = (25, 25)  # Updated
    std_dev = (1.0, 2.0)  # Updated
    amplitude = 5.0
    image_size = (50, 50)

    # Generate the image
    generated_image = gaussian_image_generator.get_data(
        center=center, std_dev=std_dev, amplitude=amplitude, image_size=image_size
    )

    # Assert that the generated image has the correct dimensions
    assert generated_image.data.shape == image_size

    # Assert that the image contains positive values
    assert np.all(generated_image.data >= 0)

    # Assert that the maximum value matches the amplitude (approximately)
    assert np.isclose(generated_image.data.max(), amplitude, atol=0.1)
