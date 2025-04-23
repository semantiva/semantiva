import pytest
from semantiva.examples.test_utils import (
    FloatDataCollection,
    FloatDataType,
    FloatCollectValueProbe,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel
from semantiva.context_processors.context_processors import ModelFittingContextProcessor
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.data_processors.data_slicer_factory import Slicer


@pytest.fixture
def linear_int_data_collection(num_items=5):
    """Create a collection of FloatDataType objects with linear data."""
    data_collection = FloatDataCollection()
    for i in range(num_items):
        data_collection.append(FloatDataType(float(i)))
    return data_collection


def test_pipeline_single_string_key(linear_int_data_collection):
    """Test a pipeline with a single string key."""
    t_values = [i for i in range(len(linear_int_data_collection))]
    node_configurations = [
        {
            "processor": Slicer(FloatCollectValueProbe, FloatDataCollection),
            "context_keyword": "data_values",
        },
        {
            "processor": ModelFittingContextProcessor,
            "parameters": {
                "fitting_model": PolynomialFittingModel(degree=1),
                "independent_var_key": "t_values",
                "dependent_var_key": "data_values",
                "context_keyword": "fit_coefficients",
            },
        },
    ]
    pipeline = Pipeline(node_configurations)
    context_dict = {"t_values": t_values}
    _, output_context = pipeline.process(linear_int_data_collection, context_dict)
    assert "fit_coefficients" in output_context.keys()
    print(output_context.get_value("fit_coefficients"))
