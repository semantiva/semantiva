import pytest
from semantiva.data_operations.data_operations import FeatureExtractorProbeWrapper
from semantiva.specializations.image.image_probes import TwoDGaussianFitterProbe
from semantiva.data_operations.data_operations import (
    create_data_collection_feature_extraction_probe,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
    ParametricImageStackGenerator,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel

# === Pytest Fixtures ===


@pytest.fixture
def image_stack_generator():
    """
    Creates an image stack generator that simulates Gaussian blobs evolving over time.
    """
    return ParametricImageStackGenerator(
        num_frames=3,
        parametric_expressions={
            "center": "(350 + 200 * t, 625 - 100 * t + 100 * t ** 2)",  # Quadratic motion in y-direction
            "std_dev": "30 + 20 * t",  # Standard deviation increases linearly over frames
            "amplitude": "100",  # Fixed amplitude for all frames
        },
        param_ranges={"t": (-1, 2)},  # Time range
        image_generator=TwoDGaussianImageGenerator(),
        image_generator_params={"image_size": (1024, 1024)},  # Image resolution
    )


@pytest.fixture
def image_stack(image_stack_generator):
    """Generates an image stack using the fixture-based generator."""
    return image_stack_generator.get_data()


@pytest.fixture
def time_values(image_stack_generator):
    """Provides the computed time values associated with each frame."""
    return image_stack_generator.t_values


@pytest.fixture
def extracted_features(image_stack):
    """
    Extracts all relevant features (peak center and std deviation) in a single call to improve performance.
    """
    multi_feature_probe = create_data_collection_feature_extraction_probe(
        FeatureExtractorProbeWrapper(
            TwoDGaussianFitterProbe, param_key=("peak_center", "std_dev_x", "std_dev_y")
        )
    )()

    return multi_feature_probe.process(image_stack)


# === Combined Polynomial Fitting Tests ===


def assert_close(expected, actual, tol=1e-1):
    """Helper function to compare expected and actual coefficients with a tolerance."""
    assert abs(expected - actual) < tol, f"Expected {expected}, but got {actual}"


def test_polynomial_fitting_all(time_values, extracted_features):
    """
    Tests polynomial fitting for both standard deviation and peak center (x, y).
    Uses a single extracted feature set to improve test efficiency.
    """
    extracted_std_devs = [f[1] for f in extracted_features]
    extracted_center_positions = [f[0] for f in extracted_features]

    # === Fit Standard Deviation to Linear Model ===
    std_dev_model = PolynomialFittingModel(degree=1)
    std_dev_fit_params = std_dev_model.fit(time_values, extracted_std_devs)

    expected_std_dev_params = {"coeff_0": 30, "coeff_1": 20}
    assert (
        std_dev_fit_params.keys() == expected_std_dev_params.keys()
    ), "Mismatch in std_dev coefficients"
    for key in expected_std_dev_params:
        assert_close(expected_std_dev_params[key], std_dev_fit_params[key])

    # === Fit X-Center to Linear Model ===
    x_positions = [center[0] for center in extracted_center_positions]
    x_center_model = PolynomialFittingModel(degree=1)
    x_center_fit_params = x_center_model.fit(time_values, x_positions)

    expected_x_params = {"coeff_0": 350, "coeff_1": 200}
    assert (
        x_center_fit_params.keys() == expected_x_params.keys()
    ), "Mismatch in x_center coefficients"
    for key in expected_x_params:
        assert_close(expected_x_params[key], x_center_fit_params[key])

    # === Fit Y-Center to Quadratic Model ===
    y_positions = [center[1] for center in extracted_center_positions]
    y_center_model = PolynomialFittingModel(degree=2)
    y_center_fit_params = y_center_model.fit(time_values, y_positions)

    expected_y_params = {"coeff_0": 625, "coeff_1": -100, "coeff_2": 100}
    assert (
        y_center_fit_params.keys() == expected_y_params.keys()
    ), "Mismatch in y_center coefficients"
    for key in expected_y_params:
        assert_close(expected_y_params[key], y_center_fit_params[key])
