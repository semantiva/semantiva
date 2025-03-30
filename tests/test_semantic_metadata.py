import pytest
from pprint import pprint

from .test_utils import (
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatProbe,
    FloatCollectionSumOperation,
)


def print_metadata(component):
    print()
    print("Component metadata:")
    pprint(component.get_metadata())
    print("\n")
    print("Component semantic ID:")
    print(component.semantic_id())


def test_datasource_semantic_metadata():
    """Test the semantic metadata of the DataSource"""
    print_metadata(FloatDataSource)
    assert FloatDataSource.get_metadata()["output_data_type"] == "FloatDataType"


def test_payloadsource_semantic_metadata():
    """Test the semantic metadata of the PayloadSource"""
    print_metadata(FloatPayloadSource)

    assert FloatPayloadSource.get_metadata()["output_data_type"] == "FloatDataType"
    assert FloatPayloadSource.get_metadata()["injected_context_keys"] == "None"


def test_datasink_semantic_metadata():
    """Test the semantic metadata of the DataSink"""
    print_metadata(FloatDataSink)
    assert FloatDataSink.get_metadata()["input_data_type"] == "FloatDataType"


def test_payloadsink_semantic_metadata():
    """Test the semantic metadata of the PayloadSink"""
    assert FloatPayloadSink.get_metadata()["input_data_type"] == "FloatDataType"


def test_float_multiply_operation_semantic_metadata():
    """Test the semantic metadata of the FloatMultiplyOperation"""
    print_metadata(FloatMultiplyOperation)
    assert FloatMultiplyOperation.get_metadata()["input_data_type"] == "FloatDataType"
    assert FloatMultiplyOperation.get_metadata()["output_data_type"] == "FloatDataType"
    assert FloatMultiplyOperation.get_metadata()["input_parameters"] == [
        "factor: float"
    ]


# test FloatProbe
def test_float_probe_semantic_metadata():
    """Test the semantic metadata of the FloatProbe"""
    print_metadata(FloatProbe)
    assert FloatProbe.get_metadata()["input_data_type"] == "FloatDataType"
    assert FloatProbe.get_metadata()["input_parameters"] == "None"


def test_float_collection_sum_operation_semantic_metadata():
    """Test the semantic metadata of the FloatCollectionSumOperation"""
    print_metadata(FloatCollectionSumOperation)
    assert (
        FloatCollectionSumOperation.get_metadata()["input_data_type"]
        == "FloatDataCollection"
    )
    assert (
        FloatCollectionSumOperation.get_metadata()["output_data_type"]
        == "FloatDataType"
    )
    assert FloatCollectionSumOperation.get_metadata()["input_parameters"] == "None"
