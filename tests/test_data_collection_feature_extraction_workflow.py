import pytest
from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
    ParametricImageStackGenerator,
)
from semantiva.workflows.feature_extraction import feature_extract_and_fit
from semantiva.specializations.image.image_probes import (
    ImageProbe,
    TwoDGaussianFitterProbe,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel


class TwoDGaussianStdDevProbe(ImageProbe):
    def _operation(self, data):
        gaussian_fitter_probe = TwoDGaussianFitterProbe()
        std_dev = gaussian_fitter_probe.process(data)["std_dev_x"]
        return std_dev


@pytest.fixture
def image_stack_generator():
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
    return generator


def test_feature_extraction_and_fitting_with_std_dev_probe(image_stack_generator):
    image_stack = image_stack_generator.get_data()
    t_values = image_stack_generator.t_values

    std_dev_fitting_results = feature_extract_and_fit(
        data=image_stack,
        operation=TwoDGaussianStdDevProbe,
        fitting_model=PolynomialFittingModel(degree=1),
        independent_variable=t_values,
    )

    assert std_dev_fitting_results is not None
    assert len(std_dev_fitting_results) == 2


def test_feature_extraction_and_fitting_with_fitter_probe(image_stack_generator):
    image_stack = image_stack_generator.get_data()
    t_values = image_stack_generator.t_values

    std_dev_fitting_results = feature_extract_and_fit(
        data=image_stack,
        operation=TwoDGaussianFitterProbe,
        fitting_model=PolynomialFittingModel(degree=1),
        independent_variable=t_values,
        probe_param_key="std_dev_x",
    )

    assert std_dev_fitting_results is not None
    assert len(std_dev_fitting_results) == 2
