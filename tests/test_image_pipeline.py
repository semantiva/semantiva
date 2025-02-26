import pytest
from semantiva.logger import Logger
from semantiva.context_operations.context_types import ContextType
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
)
from semantiva.payload_operations import Pipeline
from semantiva.specializations.image.image_operations import (
    ImageAddition,
    StackToImageMeanProjector,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
)


@pytest.fixture
def image_stack_data():
    """
    Pytest fixture for providing an ImageStackDataType instance using the dummy generator.
    """
    generator = ImageStackRandomGenerator()
    return generator.get_data((10, 256, 256))


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


def test_image_pipeline_execution(image_stack_data, random_image1, random_image2):
    """
    Test the execution of a pipeline with multiple image operations.

    The pipeline consists of:
    1. StackToImageMeanProjector: Flattens the image stack to a 2D image.
    2. ImageAddition: Adds a random image to the flattened image.
    3. ImageSubtraction: Subtracts another random image from the result.
    4. ImageCropper: Clips the final image to a specific region.
    """
    # Define node configurations
    node_configurations = [
        {
            "operation": "StackToImageMeanProjector",
            "parameters": {},
        },
        {
            "operation": "ImageAddition",
            "parameters": {"image_to_add": random_image1},
        },
        {
            "operation": "ImageSubtraction",
            "parameters": {"image_to_subtract": random_image2},
        },
        {
            "operation": "ImageCropper",
            "parameters": {"x_start": 50, "x_end": 200, "y_start": 50, "y_end": 200},
        },
    ]

    # Initialize logger
    logger = Logger()
    logger.set_verbose_level("DEBUG")
    logger.set_console_output()
    # Initialize the pipeline
    pipeline = Pipeline(node_configurations, logger)

    # Initialize the context and process the data
    context = ContextType()
    output_data, output_context = pipeline.process(image_stack_data, context)

    # Validate the output
    assert isinstance(output_data, ImageDataType)
    assert isinstance(output_context, ContextType)
    # Expected result validation skipped due to dynamic random inputs

    # Inspect the pipeline
    print("\n")
    print(
        "==============================Pipeline inspection=============================="
    )
    print(pipeline.inspect())

    # Check timers
    print(
        "================================Pipeline timers================================"
    )
    print(pipeline.get_timers())
    print(
        "==============================================================================="
    )
