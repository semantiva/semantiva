import pytest
from semantiva.execution_tools.tasks import PayloadOperationTask
from semantiva.context_operations.context_types import ContextType
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageStackPayloadRandomGenerator,
    ImageDataRandomGenerator,
)
from semantiva.specializations.image.image_algorithms import (
    ImageAddition,
    ImageSubtraction,
    ImageClipping,
    StackToImageMeanProjector,
)
from semantiva.payload_operations import Pipeline
from semantiva.specializations.image.image_data_types import ImageDataType


@pytest.fixture
def random_image1():
    """
    Pytest fixture for providing a random 2D ImageDataType instance using the dummy generator.
    """
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


@pytest.fixture
def random_image2():
    """
    Pytest fixture for providing another random 2D ImageDataType instance using the dummy generator.
    """
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


def test_pipeline_task(random_image1, random_image2):
    """Test pipeline task"""

    node_configurations = [
        {
            "operation": StackToImageMeanProjector,
            "parameters": {},
        },
        {
            "operation": ImageAddition,
            "parameters": {"image_to_add": random_image1},
        },
        {
            "operation": ImageSubtraction,
            "parameters": {"image_to_subtract": random_image2},
        },
        {
            "operation": ImageClipping,
            "parameters": {"x_start": 50, "x_end": 200, "y_start": 50, "y_end": 200},
        },
    ]

    payload_task = PayloadOperationTask(
        ImageStackPayloadRandomGenerator, {}, Pipeline, node_configurations
    )

    updated_data, updated_context = payload_task.run()
    assert isinstance(updated_data, ImageDataType)
    assert isinstance(updated_context, ContextType)
