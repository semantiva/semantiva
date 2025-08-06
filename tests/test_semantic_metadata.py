# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pprint import pprint

from semantiva.examples.test_utils import (
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
    assert FloatPayloadSource.get_metadata()["injected_context_keys"] == []


def test_datasink_semantic_metadata():
    """Test the semantic metadata of the DataSink"""
    print_metadata(FloatDataSink)
    assert FloatDataSink.get_metadata()["input_data_type"] == "FloatDataType"


def test_payloadsink_semantic_metadata():
    """Test the semantic metadata of the PayloadSink"""
    print_metadata(FloatPayloadSink)
    assert FloatPayloadSink.get_metadata()["input_data_type"] == "FloatDataType"
    # Verify that 'payload' is not listed as a required parameter
    assert FloatPayloadSink.get_metadata()["parameters"] == "None"


def test_float_multiply_operation_semantic_metadata():
    """Test the semantic metadata of the FloatMultiplyOperation"""
    print_metadata(FloatMultiplyOperation)
    assert FloatMultiplyOperation.get_metadata()["input_data_type"] == "FloatDataType"
    assert FloatMultiplyOperation.get_metadata()["output_data_type"] == "FloatDataType"
    params = FloatMultiplyOperation.get_metadata()["parameters"]
    assert "factor" in params
    assert params["factor"].annotation == "float"


# test FloatProbe
def test_float_probe_semantic_metadata():
    """Test the semantic metadata of the FloatProbe"""
    print_metadata(FloatProbe)
    assert FloatProbe.get_metadata()["input_data_type"] == "FloatDataType"
    assert FloatProbe.get_metadata()["parameters"] == {}


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
    assert FloatCollectionSumOperation.get_metadata()["parameters"] == {}
