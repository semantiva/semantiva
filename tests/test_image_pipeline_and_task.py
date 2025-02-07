import pytest
from semantiva.execution_tools.tasks import PayloadOperationTask
from semantiva.context_operations.context_types import ContextType
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
    ImageStackPayloadRandomGenerator,
)
from semantiva.specializations.image.image_algorithms import (
    ImageAddition,
    ImageSubtraction,
    ImageClipping,
    StackToImageMeanProjector,
)
from semantiva.payload_operations import Pipeline
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
)


@pytest.fixture
def random_image():
    """
    Pytest fixture providing a random 2D ImageDataType instance.
    """
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


@pytest.fixture
def another_random_image():
    """
    Pytest fixture providing another random 2D ImageDataType instance.
    """
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


@pytest.fixture
def random_image_stack():
    """
    Pytest fixture providing a random 3D ImageStackDataType instance (stack of 5 images).
    """
    generator = ImageStackRandomGenerator()
    return generator.get_data((5, 256, 256))  # Generates a stack of 5 images


def test_pipeline_task(random_image, another_random_image):
    """
    Tests a complete pipeline execution with multiple operations.

    - The first node (`StackToImageMeanProjector`) reduces the stack to a single `ImageDataType`.
    - The following nodes (`ImageAddition`, `ImageSubtraction`, `ImageClipping`) modify the image.
    - The final output should be a single `ImageDataType`.
    """

    node_configurations = [
        {
            "operation": StackToImageMeanProjector,
            "parameters": {},
        },
        {
            "operation": ImageAddition,
            "parameters": {"image_to_add": random_image},
        },
        {
            "operation": ImageSubtraction,
            "parameters": {"image_to_subtract": another_random_image},
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

    # Validate that the output is an ImageDataType
    assert isinstance(
        updated_data, ImageDataType
    ), "Pipeline output should be an ImageDataType"

    # Validate that the output context is still a ContextType
    assert isinstance(
        updated_context, ContextType
    ), "Updated context should be of type ContextType"


def test_pipeline_slicing(random_image_stack, random_image, another_random_image):
    """
    Tests the pipeline's ability to correctly slice a DataCollection when required.

    - The input (`ImageStackDataType`) contains a collection of `ImageDataType` elements.
    - The pipeline processes each `ImageDataType` individually via slicing.
    - The final output should remain an `ImageStackDataType` with the same number of images.
    """

    node_configurations = [
        {
            "operation": ImageAddition,
            "parameters": {"image_to_add": random_image},
        },
        {
            "operation": ImageSubtraction,
            "parameters": {"image_to_subtract": another_random_image},
        },
    ]

    # Initialize the pipeline
    pipeline = Pipeline(node_configurations)

    # Initialize context
    context = ContextType()

    # Process the stacked images through the pipeline
    output_data, output_context = pipeline.process(random_image_stack, context)

    # Validate that the output is still an ImageStackDataType (stack of images)
    assert isinstance(
        output_data, ImageStackDataType
    ), "Pipeline output should be an ImageStackDataType"

    # Validate that the number of images remains unchanged
    assert (
        len(list(iter(output_data))) == 5
    ), "Output ImageStackDataType should contain 5 images"

    # Validate that each element in the stack is an ImageDataType
    for img in output_data:
        assert isinstance(
            img, ImageDataType
        ), "Each element in ImageStackDataType should be an ImageDataType"

    # Validate that the output context remains of type ContextType
    assert isinstance(
        output_context, ContextType
    ), "Updated context should be of type ContextType"
