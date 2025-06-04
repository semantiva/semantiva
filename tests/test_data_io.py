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

import pytest

from semantiva.examples.test_utils import (
    FloatDataType,
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    DummyContext,
)


# -----------------------------------------------------------------------------------
# TESTS FOR DATA SOURCE
# -----------------------------------------------------------------------------------


def test_datasource_get_data():
    """Test the get_data method of the DataSource"""
    ds = FloatDataSource()
    data = ds.get_data()
    assert isinstance(
        data, FloatDataType
    ), "DataSource did not return an FloatDataType."
    assert data.data == 123.0, "DataSource returned unexpected data value."


def test_datasource_output_data_type():
    """Test the output_data_type method of the DataSource"""
    ds = FloatDataSource()
    assert (
        ds.output_data_type() is FloatDataType
    ), "DataSource output_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR PAYLOAD SOURCE
# -----------------------------------------------------------------------------------


def test_payloadsource_get_payload():
    """Test the get_payload method of the PayloadSource"""
    ps = FloatPayloadSource()
    data, context = ps.get_payload()
    assert isinstance(
        data, FloatDataType
    ), "PayloadSource did not return an FloatDataType."
    assert isinstance(
        context, DummyContext
    ), "PayloadSource did not return a DummyContext."
    assert data.data == 456, "PayloadSource returned unexpected data value."


def test_payloadsource_output_data_type():
    """Test the output_data_type method of the PayloadSource"""
    ps = FloatPayloadSource()
    assert (
        ps.output_data_type() is FloatDataType
    ), "PayloadSource output_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR DATA SINK
# -----------------------------------------------------------------------------------


def test_datasink_send_data():
    """Test the send_data method of the DataSink"""
    sink = FloatDataSink()
    data = FloatDataType(999.0)
    sink.send_data(data)
    # Check that the sink stored the data properly
    assert (
        sink.last_data_sent is data
    ), "DataSink did not store the last data correctly."


def test_datasink_input_data_type():
    """Test the input_data_type method of the DataSink"""
    sink = FloatDataSink()
    assert sink.input_data_type() is FloatDataType, "DataSink input_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR PAYLOAD SINK
# -----------------------------------------------------------------------------------


def test_payloadsink_send_payload():
    """Test the send_payload method of the PayloadSink"""
    sink = FloatPayloadSink()
    data = FloatDataType(1001.0)
    context = DummyContext()
    sink.send_payload(data, context)
    # Check that the sink stored the payload properly
    assert sink.last_payload is data, "PayloadSink did not store the data correctly."
    assert (
        sink.last_context is context
    ), "PayloadSink did not store the context correctly."


def test_payloadsink_input_data_type():
    """Test the input_data_type method of the PayloadSink"""
    sink = FloatPayloadSink()
    assert (
        sink.input_data_type() is FloatDataType
    ), "PayloadSink input_data_type mismatch."
