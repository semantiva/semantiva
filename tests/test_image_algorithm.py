import pytest
import numpy as np
from semantiva.specializations.image.image_algorithms import (
    ImageAddition,
    ImageSubtraction,
    ImageClipping,
    StackToImageMeanProjector,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
)


@pytest.fixture
def dummy_image_data():
    """Fixture for generating dummy ImageDataType data."""
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


@pytest.fixture
def dummy_image_stack_data():
    """Fixture for generating dummy ImageStackDataType data."""
    generator = ImageStackRandomGenerator()
    return generator.get_data((10, 256, 256))


def test_image_addition(dummy_image_data):
    """Test the ImageAddition algorithm."""
    addition = ImageAddition()
    result = addition.process(dummy_image_data, dummy_image_data)

    # The result should be double the dummy data since it's added to itself
    expected = dummy_image_data.data * 2
    np.testing.assert_array_almost_equal(result.data, expected)


def test_image_subtraction(dummy_image_data):
    """Test the ImageSubtraction algorithm."""
    subtraction = ImageSubtraction()
    result = subtraction.process(dummy_image_data, dummy_image_data)

    # The result should be zero since the image is subtracted from itself
    expected = np.zeros_like(dummy_image_data.data)
    np.testing.assert_array_almost_equal(result.data, expected)


def test_image_clipping(dummy_image_data):
    """Test the ImageClipping algorithm."""
    clipping = ImageClipping()
    x_start, x_end, y_start, y_end = 50, 200, 50, 200
    result = clipping.process(dummy_image_data, x_start, x_end, y_start, y_end)

    # The result should be the clipped region
    expected = dummy_image_data.data[y_start:y_end, x_start:x_end]
    np.testing.assert_array_almost_equal(result.data, expected)


def test_stack_to_image_mean_projector(dummy_image_stack_data):
    """Test the StackToImageMeanProjector algorithm."""
    projector = StackToImageMeanProjector()
    result = projector.process(dummy_image_stack_data)

    # The result should be the mean projection along the stack's first axis
    expected = np.mean(dummy_image_stack_data.data, axis=0)
    np.testing.assert_array_almost_equal(result.data, expected)
