import pytest
import numpy as np
from semantiva.specializations.image.image_operations import (
    ImageAddition,
    ImageSubtraction,
    ImageCropper,
    StackToImageMeanProjector,
    ImageNormalizerOperation,
    ImageStackToSideBySideProjector,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
)
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
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


@pytest.fixture
def image_normalizer_operation():
    """Fixture for the ImageNormalizerOperation."""
    return ImageNormalizerOperation()


def test_image_addition(dummy_image_data):
    """Test the ImageAddition operation."""
    addition = ImageAddition()
    result = addition.process(dummy_image_data, dummy_image_data)

    # The result should be double the dummy data since it's added to itself
    expected = dummy_image_data.data * 2
    np.testing.assert_array_almost_equal(result.data, expected)


def test_image_subtraction(dummy_image_data):
    """Test the ImageSubtraction operation."""
    subtraction = ImageSubtraction()
    result = subtraction.process(dummy_image_data, dummy_image_data)

    # The result should be zero since the image is subtracted from itself
    expected = np.zeros_like(dummy_image_data.data)
    np.testing.assert_array_almost_equal(result.data, expected)


def test_image_clipping(dummy_image_data):
    """Test the ImageCropper operation."""
    clipping = ImageCropper()
    x_start, x_end, y_start, y_end = 50, 200, 50, 200
    result = clipping.process(dummy_image_data, x_start, x_end, y_start, y_end)

    # The result should be the clipped region
    expected = dummy_image_data.data[y_start:y_end, x_start:x_end]
    np.testing.assert_array_almost_equal(result.data, expected)


def test_stack_to_image_mean_projector(dummy_image_stack_data):
    """Test the StackToImageMeanProjector operation."""
    projector = StackToImageMeanProjector()
    result = projector.process(dummy_image_stack_data)

    # The result should be the mean projection along the stack's first axis
    expected = np.mean(dummy_image_stack_data.data, axis=0)
    np.testing.assert_array_almost_equal(result.data, expected)


def test_image_normalizer_operation(image_normalizer_operation):
    # Create a test image with varying pixel values
    image_data = np.array([[0, 50, 100], [150, 200, 250]], dtype=np.float32)
    image = ImageDataType(image_data)

    # Define the normalization range
    min_value, max_value = 0, 1

    # Perform normalization
    normalized_image = image_normalizer_operation.process(image, min_value, max_value)

    # Assert that the normalized values are within the expected range
    assert np.isclose(normalized_image.data.min(), min_value, atol=1e-6)
    assert np.isclose(normalized_image.data.max(), max_value, atol=1e-6)

    # Assert linear scaling
    expected_normalized = (image_data - image_data.min()) / (
        image_data.max() - image_data.min()
    ) * (max_value - min_value) + min_value
    assert np.allclose(normalized_image.data, expected_normalized, atol=1e-6)


# Pytest test suite
def test_image_stack_to_side_by_side_projector_valid():
    # Create sample image stack
    image1 = np.ones((100, 100)) * 255  # White square
    image2 = np.zeros((100, 100))  # Black square
    image3 = np.ones((100, 100)) * 128  # Gray square

    # Stack into 3D array
    image_stack = np.stack([image1, image2, image3], axis=0)
    image_stack_data = ImageStackDataType(image_stack)

    # Instantiate the projector
    projector = ImageStackToSideBySideProjector()

    # Perform projection
    result = projector._process_logic(image_stack_data)

    # Assert the resulting image shape
    assert result.data.shape == (
        100,
        300,
    )  # Height remains, width is sum of individual widths

    # Assert pixel values are correct
    np.testing.assert_array_equal(result.data[:, :100], image1)
    np.testing.assert_array_equal(result.data[:, 100:200], image2)
    np.testing.assert_array_equal(result.data[:, 200:], image3)
