import pytest
from typing import List, Dict, Iterator, Type
from semantiva.data_types.data_types import BaseDataType, DataCollectionType
from semantiva.data_operations.data_operations import DataProbe, DataCollectionProbe
from semantiva.data_operations.data_collection_fit_probe import (
    create_collection_feature_extraction_and_fit_probe,
)
from semantiva.workflows.fitting_model import FittingModel

"""
Mocks and tests for create_collection_feature_extraction_and_fit_probe.
We verify probe creation, feature extraction, and function fitting.
Also tests error handling for missing arguments, mismatched lengths, etc.
"""


# ------------------------------------------------------------------------------
# Mock Classes
# ------------------------------------------------------------------------------


class MockBaseData(BaseDataType[float]):
    def validate(self, data: float) -> bool:
        return isinstance(data, float)


class MockCollection(DataCollectionType[MockBaseData, List[float]]):
    @classmethod
    def _initialize_empty(cls) -> List[float]:
        return list()

    def validate(self, data: List[float]) -> bool:
        return all(isinstance(item, float) for item in data)

    def __iter__(self) -> Iterator[MockBaseData]:
        for i in range(len(self._data)):
            yield MockBaseData(self._data[i])

    def __len__(self) -> int:
        return len(self._data)

    def append(self, item: MockBaseData) -> None:
        self._data.append(item.data)


class MockFeatureExtractor(DataProbe):
    """
    A mock feature extractor for single elements:
    Processes a MockBaseData instance and returns the float data directly.
    """

    @classmethod
    def input_data_type(cls):
        return MockBaseData

    def _operation(self, data: MockBaseData, *args, **kwargs) -> float:
        return data.data


class MockFittingModel(FittingModel):
    """
    A mock fitting model that simply returns
    the average of x_values and y_values as a dictionary.
    """

    def fit(self, x_values: List[float], y_values: List[float]) -> Dict[str, float]:
        if not x_values or not y_values:
            return {"mean_x": 0.0, "mean_y": 0.0}
        return {
            "mean_x": sum(x_values) / len(x_values),
            "mean_y": sum(y_values) / len(y_values),
        }


# ------------------------------------------------------------------------------
# Test Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def sample_data_collection() -> MockCollection:
    """
    Creates a MockCollection with several MockBaseData elements.
    """
    coll = MockCollection()
    for val in [1.0, 2.0, 3.0, 4.0, 5.0]:
        coll.append(MockBaseData(val))
    return coll


@pytest.fixture
def mock_feature_extractor() -> MockFeatureExtractor:
    """
    Returns a MockFeatureExtractor instance.
    """
    return MockFeatureExtractor()


@pytest.fixture
def mock_fitting_model() -> MockFittingModel:
    """
    Returns a MockFittingModel instance.
    """
    return MockFittingModel()


@pytest.fixture
def generated_probe_class(
    mock_feature_extractor: MockFeatureExtractor, mock_fitting_model: MockFittingModel
) -> Type[DataCollectionProbe[MockCollection]]:  # FIX: Correct return type
    """
    Uses the factory to create a dynamically generated probe class
    that extracts features and fits them.
    """
    GeneratedProbe: Type[DataCollectionProbe[MockCollection]] = (
        create_collection_feature_extraction_and_fit_probe(
            feature_extractor=mock_feature_extractor,
            fitting_model=mock_fitting_model,
            independent_variable_parameter_name="domain",
        )
    )
    return GeneratedProbe


@pytest.fixture
def generated_probe(
    generated_probe_class: Type[DataCollectionProbe[MockCollection]],
) -> DataCollectionProbe[MockCollection]:
    """
    Instantiates the dynamically generated probe class.
    """
    return generated_probe_class()


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------


def test_probe_creation(generated_probe_class):
    """
    Tests that we can successfully create the probe class
    without abstract method errors.
    """

    probe_instance = generated_probe_class()
    assert isinstance(probe_instance, DataCollectionProbe)
    assert hasattr(probe_instance, "fitting_model")
    assert hasattr(probe_instance, "feature_extraction_probe")


def test_feature_extraction_and_fitting(generated_probe, sample_data_collection):
    """
    Tests extracting features and fitting them with independent variables.
    """
    # Domain: lens positions or any numeric annotation
    domain = [10.0, 20.0, 30.0, 40.0, 50.0]
    results = generated_probe.process(sample_data_collection, domain=domain)
    assert isinstance(results, dict), "Expected a dictionary of fit results"

    # The mock fitting calculates mean_x and mean_y
    assert results["mean_x"] == 30.0  # average of domain
    assert results["mean_y"] == 3.0  # average of [1.0..5.0]


def test_missing_independent_variables(generated_probe, sample_data_collection):
    """
    Tests that missing domain variables cause a ValueError.
    """
    with pytest.raises(ValueError) as exc_info:
        generated_probe.process(sample_data_collection)  # no domain passed
    assert "Missing required argument 'domain'" in str(exc_info.value)


def test_mismatched_variable_lengths(generated_probe, sample_data_collection):
    """
    Tests that domain length mismatch with extracted features raises an error.
    """
    # Only 3 domain values while we have 5 data items
    domain = [10.0, 20.0, 30.0]
    with pytest.raises(ValueError) as exc_info:
        generated_probe.process(sample_data_collection, domain=domain)
    assert "Mismatch: 3 independent variables but 5 extracted features." in str(
        exc_info.value
    )


def test_empty_data_collection(generated_probe_class):
    """
    Tests handling of an empty data collection.
    """
    # Create an empty collection
    empty_collection = MockCollection()

    domain = []  # No domain values
    probe = generated_probe_class()

    # Should not raise an error because we can handle zero-length data
    results = probe.process(empty_collection, domain=domain)
    assert isinstance(results, dict), "Expected a dictionary of fit results"

    # The mock fitting model returns 0.0 for both means if domain or features are empty
    assert results["mean_x"] == 0.0
    assert results["mean_y"] == 0.0


def test_consistency_of_extracted_features(generated_probe, sample_data_collection):
    """
    Ensures that running the probe twice on the same data yields consistent results.
    """
    domain = [10.0, 20.0, 30.0, 40.0, 50.0]
    first_result = generated_probe.process(sample_data_collection, domain=domain)
    second_result = generated_probe.process(sample_data_collection, domain=domain)

    assert (
        first_result == second_result
    ), "Probe results should be consistent across multiple runs."


if __name__ == "__main__":
    pytest.main()
