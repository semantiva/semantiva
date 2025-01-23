import pytest
from semantiva.context_operations.context_types import ContextType, ContextSequenceType
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
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


@pytest.fixture
def random_context():
    """
    Pytest fixture providing a random ContextType instance.
    """
    return ContextType({"param": 42})


@pytest.fixture
def random_context_sequence():
    """
    Pytest fixture providing a ContextSequenceType with 5 distinct context items.
    """
    return ContextSequenceType([ContextType({"param": i}) for i in range(5)])


def test_pipeline_slicing_with_single_context(
    random_image_stack, random_image, another_random_image, random_context
):
    """
    Tests slicing when using a single ContextType.

    - The `ImageStackDataType` is sliced into `ImageDataType` items.
    - The **same** ContextType instance is passed to each sliced item.
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

    pipeline = Pipeline(node_configurations)

    output_data, output_context = pipeline.process(random_image_stack, random_context)

    assert isinstance(
        output_data, ImageStackDataType
    ), "Output should be an ImageStackDataType"
    assert len(output_data) == 5, "ImageStackDataType should retain 5 images"
    assert isinstance(
        output_context, ContextType
    ), "Context should remain a ContextType"


def test_pipeline_slicing_with_context_sequence(
    random_image_stack, random_image, another_random_image, random_context_sequence
):
    """
    Tests slicing when using a ContextSequenceType.

    - The `ImageStackDataType` is sliced into `ImageDataType` items.
    - A **corresponding** `ContextType` is used for each sliced item.
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

    pipeline = Pipeline(node_configurations)

    output_data, output_context = pipeline.process(
        random_image_stack, random_context_sequence
    )

    assert isinstance(
        output_data, ImageStackDataType
    ), "Output should be an ImageStackDataType"
    assert len(output_data) == 5, "ImageStackDataType should retain 5 images"
    assert isinstance(
        output_context, ContextSequenceType
    ), "Context should remain a ContextSequenceType"
    assert len(output_context) == 5, "ContextSequenceType should retain 5 items"


def test_pipeline_without_slicing(random_image, another_random_image, random_context):
    """
    Tests normal execution without slicing.

    - The pipeline receives a **single** `ImageDataType`, so no slicing occurs.
    - The entire image is processed in one pass.
    - The final output remains a **single** `ImageDataType`.
    """

    node_configurations = [
        {
            "operation": ImageAddition,
            "parameters": {"image_to_add": another_random_image},
        },
        {
            "operation": ImageClipping,
            "parameters": {"x_start": 50, "x_end": 200, "y_start": 50, "y_end": 200},
        },
    ]

    pipeline = Pipeline(node_configurations)

    output_data, output_context = pipeline.process(random_image, random_context)

    assert isinstance(output_data, ImageDataType), "Output should be an ImageDataType"
    assert isinstance(
        output_context, ContextType
    ), "Context should remain a ContextType"


def test_pipeline_invalid_slicing(random_image, random_context):
    """
    Tests invalid slicing scenario.

    - The pipeline expects an `ImageStackDataType` but receives `ImageDataType`.
    - This should raise a **TypeError** due to incompatible pipeline topology.
    """

    node_configurations = [
        {
            "operation": StackToImageMeanProjector,
            "parameters": {},
        },
    ]

    pipeline = Pipeline(node_configurations)

    with pytest.raises(TypeError):
        pipeline.process(random_image, random_context)
