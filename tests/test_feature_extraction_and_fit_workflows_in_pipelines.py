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
    def _operation(self, data):
        gaussian_fitter_probe = TwoDGaussianFitterProbe()
        std_dev = gaussian_fitter_probe.process(data)["std_dev_x"]
        return std_dev


@pytest.fixture
def image_stack():
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
