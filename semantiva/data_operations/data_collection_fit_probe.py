from typing import Any, List, Type, TypeVar, Generic, Dict, Optional

from ..data_types.data_types import BaseDataType, DataCollectionType
from ..logger import Logger
from ..workflows.fitting_model import FittingModel
from .data_operations import (
    DataProbe,
    DataCollectionProbe,
    create_data_collection_feature_extraction_probe,
)


CollectionBaseType = TypeVar("CollectionBaseType", bound=BaseDataType)
IndependentVarType = TypeVar("IndependentVarType")  # Domain variable type
ExtractedFeatureType = TypeVar("ExtractedFeatureType")  # Feature type


def create_collection_feature_extraction_and_fit_probe(
    feature_extractor: DataProbe,
    fitting_model: FittingModel,
    independent_variable_parameter_name: str,
) -> Type[DataProbe]:
    """
    Factory function to create a `CollectionFeatureExtractionAndFitProbe` class.

    This probe integrates:
    - **Feature extraction** from a `DataCollectionType`.
    - **Function fitting** using a `FittingModel`.
    - **Dynamic injection of independent variables** (annotations) at runtime.

    Args:
        feature_extractor (DataProbe): The probe for extracting features.
        fitting_model (FittingModel): The model used for function fitting.
        independent_variable_parameter_name (str): Runtime argument key for passing independent variables.

    Returns:
        Type[DataCollectionProbe[CollectionBaseType, ExtractedFeatureType]]:
            A dynamically generated class that can process data collections.
    """

    class GeneratedCollectionFeatureExtractionAndFitProbe(
        DataProbe,
        Generic[IndependentVarType, ExtractedFeatureType],
    ):
        """
        A dynamically created probe that extracts features and fits a function.

        Attributes:
            feature_extraction_probe (DataCollectionFeatureExtractionProbe): Extracts features from data collections.
            fitting_model (FittingModel): Performs function fitting.
        """

        def __init__(self, logger: Optional[Logger] = None):
            """
            Initializes the probe for feature extraction and function fitting.

            Args:
                logger (Logger, optional): Logger instance. Defaults to a new instance if None.
            """
            super().__init__(logger=logger or Logger())
            self.fitting_model = fitting_model
            self.feature_extraction_probe = feature_extractor

        def _operation(self, data: CollectionBaseType, **kwargs: Any) -> Dict[str, Any]:
            """
            Extracts features, associates them with independent variables, and fits a model.

            Args:
                data (CollectionBaseType): The input data collection.
                **kwargs: Must contain the independent variables under `independent_variable_parameter_name`.

            Returns:
                Dict[str, Any]: The estimated model parameters.
            """
            if independent_variable_parameter_name not in kwargs:
                raise ValueError(
                    f"Missing required argument '{independent_variable_parameter_name}' "
                    "for independent variables."
                )

            # Retrieve independent variables from runtime parameters
            independent_vars: List[IndependentVarType] = kwargs[
                independent_variable_parameter_name
            ]

            # Extract features from the collection
            extracted_features: List[ExtractedFeatureType] = (
                self.feature_extraction_probe.process(data)
            )

            # Ensure the number of independent variables matches extracted features
            if len(independent_vars) != len(extracted_features):
                raise ValueError(
                    f"Mismatch: {len(independent_vars)} independent variables "
                    f"but {len(extracted_features)} extracted features."
                )

            # Fit the extracted features against the independent variables
            fit_results = self.fitting_model.fit(independent_vars, extracted_features)
            return fit_results

        @classmethod
        def input_data_type(cls) -> Type[DataCollectionType]:
            """Defines the expected input data type."""
            return DataCollectionType

    return GeneratedCollectionFeatureExtractionAndFitProbe
