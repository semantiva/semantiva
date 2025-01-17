import pytest
import os
import numpy as np
from semantiva.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
)
from semantiva.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
    NpzImageDataTypeLoader,
    NpzImageStackDataLoader,
    PngImageLoader,
    NpzImageDataSaver,
    NpzImageStackDataSaver,
    PngImageSaver,
)


@pytest.fixture
def sample_image_data():
    """
    Fixture to provide a sample ImageDataType using the dummy generator.
    """
    generator = ImageDataRandomGenerator()
    return generator.get_data((256, 256))


@pytest.fixture
def sample_stack_data():
    """
    Fixture to provide a sample ImageStackDataType using the dummy generator.
    """
    generator = ImageStackRandomGenerator()
    return generator.get_data((10, 256, 256))


@pytest.fixture
def tmp_test_dir(tmp_path):
    """
    Fixture to provide a temporary directory for creating test files.
    """
    return str(tmp_path)


def test_npz_image_loader(sample_image_data, tmp_test_dir):
    """
    Test loading ImageDataType from a dynamically created .npz file.
    """
    # Save the generated image to a .npz file
    file_path = os.path.join(tmp_test_dir, "image_data.npz")
    saver = NpzImageDataSaver()
    saver.send_data(sample_image_data, file_path)

    # Load the image back and verify
    loader = NpzImageDataTypeLoader()
    image_data = loader.get_data(file_path)
    assert isinstance(image_data, ImageDataType)
    assert np.array_equal(image_data.data, sample_image_data.data)


def test_npz_stack_loader(sample_stack_data, tmp_test_dir):
    """
    Test loading ImageStackDataType from a dynamically created .npz file.
    """
    # Save the generated stack to a .npz file
    file_path = os.path.join(tmp_test_dir, "stack_data.npz")
    saver = NpzImageStackDataSaver()
    saver.send_data(sample_stack_data, file_path)

    # Load the stack back and verify
    loader = NpzImageStackDataLoader()
    stack_data = loader.get_data(file_path)
    assert isinstance(stack_data, ImageStackDataType)
    assert np.array_equal(stack_data.data, sample_stack_data.data)


def test_png_image_loader(sample_image_data, tmp_test_dir):
    """
    Test loading ImageDataType from a dynamically created .png file.
    """
    # Save the generated image to a .png file
    file_path = os.path.join(tmp_test_dir, "image_data.png")
    saver = PngImageSaver()
    saver.send_data(sample_image_data, file_path)

    # Load the image back and verify
    loader = PngImageLoader()
    image_data = loader.get_data(file_path)
    assert isinstance(image_data, ImageDataType)
    assert image_data.data.shape == sample_image_data.data.shape
