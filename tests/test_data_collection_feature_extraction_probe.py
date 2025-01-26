import pytest
import numpy as np
from semantiva.specializations.image.image_data_types import ImageStackDataType
from semantiva.specializations.image.image_probes import ImageProbe
from semantiva.data_operations.data_operations import (
    DataCollectionFeatureExtractionProbe,
    create_data_collection_feature_extraction_probe,
)


class TotalImageIntensityProbe(ImageProbe):
    """
    A basic image probe that computes the total intensity of an image.

    This class provides a simple probe to calculate the sum of pixel values.
    """

    def _operation(self, data):
        """


        Args:
            data (ImageDataType): The input image data.

        Returns:
            float: sum of pixel values.
        """
        return float(data.data.sum())


@pytest.fixture
def sample_image_stack():
    """
    Pytest fixture to create a sample ImageStackDataType with 5 random images.
    Each image has dimensions 256x256.
    """
    random_images = np.random.rand(5, 256, 256)  # Stack of 5 random images
    return ImageStackDataType(random_images)


@pytest.fixture
def total_intensity_probe():
    """
    Pytest fixture to create a TotalImageIntensityProbe instance.
    """
    return TotalImageIntensityProbe()


@pytest.fixture
def collection_probe(total_intensity_probe):
    """
    Pytest fixture to create a DataCollectionFeatureExtractionProbe
    using the TotalImageIntensityProbe.
    """
    return create_data_collection_feature_extraction_probe(total_intensity_probe)()


def test_data_collection_feature_extraction_probe_creation(total_intensity_probe):
    """
    Test the creation of a DataCollectionFeatureExtractionProbe using the factory function.
    Ensures that the generated probe correctly wraps the provided feature extractor.
    """
    probe = create_data_collection_feature_extraction_probe(total_intensity_probe)()

    assert isinstance(probe, DataCollectionFeatureExtractionProbe)
    assert probe.feature_extractor is total_intensity_probe


def test_data_collection_feature_extraction_probe_execution(
    collection_probe, sample_image_stack
):
    """
    Test the execution of DataCollectionFeatureExtractionProbe.
    Ensures that features are correctly extracted from the image stack.
    """
    extracted_features = collection_probe.process(sample_image_stack)

    assert isinstance(
        extracted_features, list
    ), "Output should be a list of extracted features."
    assert len(extracted_features) == len(
        sample_image_stack
    ), "Feature count should match the number of images."
    assert all(
        isinstance(val, float) for val in extracted_features
    ), "Each extracted feature should be a float."

    # Verify the extracted values are reasonable (sum of pixel intensities should be positive)
    assert all(
        val > 0 for val in extracted_features
    ), "Total intensity should be a positive value."


def test_empty_data_collection_feature_extraction(collection_probe):
    """
    Test the case where an empty ImageStackDataType is passed to the feature extraction probe.
    Ensures that an empty list is returned.
    """
    empty_stack = ImageStackDataType(np.empty((0, 256, 256)))  # Empty image stack
    extracted_features = collection_probe.process(empty_stack)

    assert (
        extracted_features == []
    ), "Processing an empty collection should return an empty list."


def test_consistency_of_extracted_features(collection_probe, sample_image_stack):
    """
    Test that feature extraction is deterministic and consistent.
    Running the probe twice on the same data should yield the same results.
    """
    first_run = collection_probe.process(sample_image_stack)
    second_run = collection_probe.process(sample_image_stack)

    assert first_run == second_run, "Feature extraction should be deterministic."


if __name__ == "__main__":
    pytest.main()
