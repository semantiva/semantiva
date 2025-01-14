import pytest
import numpy as np
from semantic_framework.specializations.image.image_data_types import (
    ImageDataType,
    ImageStackDataType,
)
from semantic_framework.specializations.image.image_loaders_savers_generators import (
    ImageDataRandomGenerator,
    ImageStackRandomGenerator,
    NpzImageDataTypeLoader,
    NpzImageStackDataLoader,
    PngImageLoader,
    ImageDataDummySink,
    ImageStackDummySink,
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
def test_data_dir():
    """
    Fixture to provide the path to the test data directory.
    """
    return "tests/data"


def test_npz_image_loader(test_data_dir):
    """
    Test loading ImageDataType from an .npz file.
    """
    loader = NpzImageDataTypeLoader()
    image_data = loader.get_data(f"{test_data_dir}/image_data.npz")
    assert isinstance(image_data, ImageDataType)
    assert image_data.data.shape == (256, 256)


def test_npz_stack_loader(test_data_dir):
    """
    Test loading ImageStackDataType from an .npz file.
    """
    loader = NpzImageStackDataLoader()
    stack_data = loader.get_data(f"{test_data_dir}/stack_data.npz")
    assert isinstance(stack_data, ImageStackDataType)
    assert stack_data.data.shape == (10, 256, 256)


def test_png_image_loader(test_data_dir):
    """
    Test loading ImageDataType from a .png file.
    """
    loader = PngImageLoader()
    image_data = loader.get_data(f"{test_data_dir}/image_data.png")
    assert isinstance(image_data, ImageDataType)
    assert image_data.data.shape == (256, 256)


def test_dummy_image_data_type_sink(sample_image_data):
    """Test DummyImageDataTypeSink with valid and invalid inputs."""
    sink = ImageDataDummySink()

    # Valid input
    sink.send_data(sample_image_data)

    # Invalid input
    with pytest.raises(ValueError):
        sink.send_data(ImageStackDataType(np.random.rand(10, 256, 256)))


def test_dummy_image_stack_data_type_sink(sample_stack_data):
    """Test DummyImageStackDataTypeSink with valid and invalid inputs."""
    sink = ImageStackDummySink()

    # Valid input
    sink.send_data(sample_stack_data)

    # Invalid input
    with pytest.raises(ValueError):
        sink.send_data(ImageDataType(np.random.rand(256, 256)))
