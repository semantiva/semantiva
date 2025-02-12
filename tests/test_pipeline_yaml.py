import pytest
from semantiva.payload_operations import Pipeline
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageStackRandomGenerator,
)
from semantiva.specializations.image.image_data_types import ImageStackDataType
from semantiva.configurations.load_pipeline_from_yaml import load_pipeline_from_yaml
from semantiva.context_operations.context_types import ContextType


@pytest.fixture
def random_image_stack():
    """
    Pytest fixture providing a random 3D ImageStackDataType instance (stack of 5 images).
    """
    generator = ImageStackRandomGenerator()
    return generator.get_data((5, 256, 256))  # Generates a stack of 5 images


@pytest.fixture
def yaml_config_path():
    """Pytest fixture providing the path to a YAML configuration file."""
    return "tests/pipeline_config.yaml"


@pytest.fixture
def context_type():
    """Pytest fixture providing a dummy context."""
    return ContextType({"dummy": 1})


def test_pipeline_yaml(random_image_stack, yaml_config_path, context_type):
    """Test the pipeline processing using a YAML configuration file."""

    load_pipeline_config = load_pipeline_from_yaml(yaml_config_path)
    print(load_pipeline_config)
    pipeline = Pipeline(load_pipeline_config)

    data, context = pipeline.process(random_image_stack, context_type)

    assert "final_info" in context.keys
    assert "dummy" not in context.keys
    assert isinstance(data, ImageStackDataType)
