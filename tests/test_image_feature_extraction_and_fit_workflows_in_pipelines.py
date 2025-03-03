import pytest
from semantiva.specializations.image.image_probes import TwoDGaussianFitterProbe
from semantiva.workflows.fitting_model import PolynomialFittingModel
from semantiva.context_processors.context_processors import ModelFittingContextProcessor
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.specializations.image.image_probes import ImageProbe

from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
    ParametricImageStackGenerator,
)


class TwoDGaussianStdDevProbe(ImageProbe):
    """A probe to extract the standard deviation of a 2D Gaussian from an image."""

    def _process_logic(self, data):
        gaussian_fitter_probe = TwoDGaussianFitterProbe()
        std_dev = gaussian_fitter_probe.process(data)["std_dev_x"]
        return std_dev


@pytest.fixture
def image_stack():
    """Fixture to provide a sample image stack with 3 frames using smaller images."""
    generator = ParametricImageStackGenerator(
        num_frames=3,
        parametric_expressions={
            "x_0": "50 + 5 * t",  # Adjusted peak x position to remain within a 128px image
            "y_0": "50 + 5 * t",  # Adjusted peak y position accordingly
            "std_dev": "10 + 2 * t",  # Reduced standard deviation for a smaller image
            "amplitude": "100",
        },
        param_ranges={"t": (-1, 2)},
        image_generator=TwoDGaussianImageGenerator(),
        image_generator_params={
            "image_size": (128, 128)
        },  # Use a much smaller image size
    )
    return generator.get_data(), generator.t_values


def test_pipeline_single_string_key(image_stack):
    """Test a pipeline with a single string key for dependent_var_key."""
    image_data, t_values = image_stack
    node_configurations = [
        {
            "processor": TwoDGaussianStdDevProbe,
            "context_keyword": "std_dev_features",
        },
        {
            "processor": ModelFittingContextProcessor,
            "parameters": {
                "fitting_model": PolynomialFittingModel(degree=1),
                "independent_var_key": "t_values",
                "dependent_var_key": "std_dev_features",
                "context_keyword": "std_dev_coefficients",
            },
        },
    ]
    pipeline = Pipeline(node_configurations)
    context_dict = {"t_values": t_values}
    output_data, output_context = pipeline.process(image_data, context_dict)
    assert "std_dev_coefficients" in output_context.keys()


def test_pipeline_tuple_key(image_stack):
    """Test a pipeline with a tuple key for dependent_var_key."""
    image_data, t_values = image_stack
    node_configurations = [
        {
            "processor": TwoDGaussianFitterProbe,
            "context_keyword": "gaussian_fit_parameters",
        },
        {
            "processor": ModelFittingContextProcessor,
            "parameters": {
                "fitting_model": PolynomialFittingModel(degree=1),
                "independent_var_key": "t_values",
                "dependent_var_key": ("gaussian_fit_parameters", "std_dev_x"),
                "context_keyword": "std_dev_coefficients",
            },
        },
    ]
    pipeline = Pipeline(node_configurations)
    context_dict = {"t_values": t_values}
    output_data, output_context = pipeline.process(image_data, context_dict)
    assert "std_dev_coefficients" in output_context.keys()
