import pytest
from typing import Tuple

from semantiva.data_types.data_types import BaseDataType, DataCollectionType
from semantiva.context_operations import ContextType
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from .test_utils import IntDataType


# -----------------------------------------------------------------------------------
# DUMMY IMPLEMENTATIONS FOR TESTING
# -----------------------------------------------------------------------------------


class DummyContext(ContextType):
    """
    Minimal stand-in for a context type.
    """

    pass


class IntDataSource(DataSource):
    """
    Concrete implementation of DataSource
    providing IntDataType data.
    """

    def _get_data(self, *args, **kwargs) -> IntDataType:
        # Return a fixed IntDataType for testing
        return IntDataType(123)

    def output_data_type(self):
        # Return the type of data we are providing
        return IntDataType


class IntPayloadSource(PayloadSource):
    """
    Concrete implementation of PayloadSource
    providing (IntDataType, DummyContext) as payload.
    """

    def _get_payload(self, *args, **kwargs) -> Tuple[IntDataType, DummyContext]:
        # Return a tuple of data and context
        return (IntDataType(456), DummyContext())

    def output_data_type(self):
        # Return the type of data in the payload
        return IntDataType


class IntDataSink(DataSink[IntDataType]):
    """
    Concrete implementation of DataSink
    accepting IntDataType data.
    """

    def __init__(self):
        self.last_data_sent = None

    def _send_data(self, data: IntDataType, *args, **kwargs):
        # Keep track of the last data we received
        self.last_data_sent = data

    def input_data_type(self):
        # Return the type of data we accept
        return IntDataType


class IntPayloadSink(PayloadSink[IntDataType]):
    """
    Concrete implementation of PayloadSink
    accepting (IntDataType, DummyContext).
    """

    def __init__(self):
        self.last_payload = None
        self.last_context = None

    def _send_payload(self, data: IntDataType, context: ContextType, *args, **kwargs):
        # Store the payload for inspection
        self.last_payload = data
        self.last_context = context

    def input_data_type(self):
        # Return the type of data we accept
        return IntDataType


# -----------------------------------------------------------------------------------
# TESTS FOR DATA SOURCE
# -----------------------------------------------------------------------------------


def test_datasource_get_data():
    """Test the get_data method of the DataSource"""
    ds = IntDataSource()
    data = ds.get_data()
    assert isinstance(data, IntDataType), "DataSource did not return an IntDataType."
    assert data.data == 123, "DataSource returned unexpected data value."


def test_datasource_output_data_type():
    """Test the output_data_type method of the DataSource"""
    ds = IntDataSource()
    assert ds.output_data_type() is IntDataType, "DataSource output_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR PAYLOAD SOURCE
# -----------------------------------------------------------------------------------


def test_payloadsource_get_payload():
    """Test the get_payload method of the PayloadSource"""
    ps = IntPayloadSource()
    data, context = ps.get_payload()
    assert isinstance(data, IntDataType), "PayloadSource did not return an IntDataType."
    assert isinstance(
        context, DummyContext
    ), "PayloadSource did not return a DummyContext."
    assert data.data == 456, "PayloadSource returned unexpected data value."


def test_payloadsource_output_data_type():
    """Test the output_data_type method of the PayloadSource"""
    ps = IntPayloadSource()
    assert (
        ps.output_data_type() is IntDataType
    ), "PayloadSource output_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR DATA SINK
# -----------------------------------------------------------------------------------


def test_datasink_send_data():
    """Test the send_data method of the DataSink"""
    sink = IntDataSink()
    data = IntDataType(999)
    sink.send_data(data)
    # Check that the sink stored the data properly
    assert (
        sink.last_data_sent is data
    ), "DataSink did not store the last data correctly."


def test_datasink_input_data_type():
    """Test the input_data_type method of the DataSink"""
    sink = IntDataSink()
    assert sink.input_data_type() is IntDataType, "DataSink input_data_type mismatch."


# -----------------------------------------------------------------------------------
# TESTS FOR PAYLOAD SINK
# -----------------------------------------------------------------------------------


def test_payloadsink_send_payload():
    """Test the send_payload method of the PayloadSink"""
    sink = IntPayloadSink()
    data = IntDataType(1001)
    context = DummyContext()
    sink.send_payload(data, context)
    # Check that the sink stored the payload properly
    assert sink.last_payload is data, "PayloadSink did not store the data correctly."
    assert (
        sink.last_context is context
    ), "PayloadSink did not store the context correctly."


def test_payloadsink_input_data_type():
    """Test the input_data_type method of the PayloadSink"""
    sink = IntPayloadSink()
    assert (
        sink.input_data_type() is IntDataType
    ), "PayloadSink input_data_type mismatch."
