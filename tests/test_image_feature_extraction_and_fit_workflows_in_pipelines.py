import pytest
from semantiva.specializations.image.image_probes import TwoDGaussianFitterProbe
from semantiva.workflows.fitting_model import PolynomialFittingModel
from semantiva.context_operations.context_operations import ModelFittingContextOperation
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.specializations.image.image_probes import ImageProbe

from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
    ParametricImageStackGenerator,
)


class TwoDGaussianStdDevProbe(ImageProbe):
    """A probe to extract the standard deviation of a 2D Gaussian from an image."""

    def _operation(self, data):
        gaussian_fitter_probe = TwoDGaussianFitterProbe()
        std_dev = gaussian_fitter_probe.process(data)["std_dev_x"]
        return std_dev


@pytest.fixture
def image_stack():
    """Fixture to provide a sample image stack with 3 frames."""
    generator = ParametricImageStackGenerator(
        num_frames=3,
        parametric_expressions={
            "center": "(350 + 200 * t, 625 - 100 * t + 100  * t ** 2)",
            "std_dev": "30 + 20 * t",
            "amplitude": "100",
        },
        param_ranges={"t": (-1, 2)},
        image_generator=TwoDGaussianImageGenerator(),
        image_generator_params={"image_size": (1024, 1024)},
    )
    return generator.get_data(), generator.t_values


def test_pipeline_single_string_key(image_stack):
    """Test a pipeline with a single string key for dependent_var_key."""
    image_data, t_values = image_stack
    node_configurations = [
        {
            "operation": TwoDGaussianStdDevProbe,
            "context_keyword": "std_dev_features",
        },
        {
            "operation": ModelFittingContextOperation,
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
            "operation": TwoDGaussianFitterProbe,
            "context_keyword": "gaussian_fit_parameters",
        },
        {
            "operation": ModelFittingContextOperation,
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
