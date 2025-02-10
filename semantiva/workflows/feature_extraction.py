from typing import Type, Any, Optional, Union, Tuple
from semantiva.data_operations.data_operations import (
    DataProbe,
    create_data_collection_feature_extraction_probe,
    FeatureExtractorProbeWrapper,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel


def feature_extract_and_fit(
    data: Any,
    operation: Type[DataProbe],
    fitting_model: PolynomialFittingModel,
    independent_variable: Any,
    probe_param_key: Optional[Union[str, Tuple[str, ...]]] = None,
):
    """
    Automates the feature extraction and fitting workflow.

    Supports cases where:
    - The probe returns a **dictionary of multiple features**, but only one (or a subset) is needed.
    - A **specific key (`probe_param_key`)** extracts the required values before fitting.

    Args:
        data (Any): Input data (e.g., image stack).
        operation (Type[DataProbe]): The probe used for feature extraction.
        fitting_model (PolynomialFittingModel): The model to fit the extracted features.
        independent_variable (Any): The independent variable values for the fitting model.
        probe_param_key (str, tuple, optional): Key(s) to extract from the probe's dictionary output.

    Returns:
        dict: Fitted model parameters.
    """
    operation_instance: DataProbe | FeatureExtractorProbeWrapper  # Mypy delight

    # Step 1: If probe_param_key is provided, wrap the probe using FeatureExtractorWrapperProbe
    if probe_param_key:
        operation_instance = FeatureExtractorProbeWrapper(operation, probe_param_key)
    else:
        operation_instance = operation()

    # Step 2: Extract features using the specified probe
    extraction_probe = create_data_collection_feature_extraction_probe(
        operation_instance
    )()
    extracted_features = extraction_probe.process(data)

    # Step 3: Fit extracted features to the model
    fit_parameters = fitting_model.fit(independent_variable, extracted_features)

    return fit_parameters
