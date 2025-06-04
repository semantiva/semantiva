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

# This file contains utility classes for testing the semantiva package.
from typing import Tuple
from semantiva.data_types import BaseDataType, DataCollectionType
from semantiva.data_processors import DataOperation, DataProbe
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink

from semantiva.context_processors import ContextType


# Concrete implementation of BaseDataType for testing
class FloatDataType(BaseDataType[float]):
    """A data type for integers."""

    def validate(self, data: float) -> bool:
        if not isinstance(data, float):
            raise TypeError("Data must be a float")
        return True


# Concrete implementation of DataCollectionType for testing
class FloatDataCollection(DataCollectionType[FloatDataType, list]):
    """A collection of FloatDataType objects."""

    @classmethod
    def _initialize_empty(cls) -> list:
        return []

    def __iter__(self):
        return iter(self._data)

    def append(self, item: FloatDataType) -> None:
        if not isinstance(item, FloatDataType):
            raise TypeError("Item must be of type FloatDataType")
        self._data.append(item)

    def __len__(self) -> int:
        return len(self._data)

    def validate(self, data):
        for item in data:
            if not isinstance(item, FloatDataType):
                raise TypeError("Data must be a list of FloatDataType objects")


# Concrete implementation of DataOperation
class FloatOperation(DataOperation):
    """An operation specialized in processing FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        return FloatDataType


class FloatCollectionMergeOperation(DataOperation):
    """An operation specialized in merging FloatDataCollection data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataCollection

    @classmethod
    def output_data_type(cls):
        return FloatDataType


# Concrete implementation of DataProbe
class FloatProbe(DataProbe):
    """A probe specialized in processing FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        return FloatDataType


class FloatMultiplyOperation(FloatOperation):
    """An operation specialized in multiplying FloatDataType data."""

    def _process_logic(self, data, factor: float, *args, **kwargs):
        return FloatDataType(data.data * factor)


class FloatCollectionSumOperation(FloatCollectionMergeOperation):
    """An operation specialized in summing FloatDataCollection data."""

    def _process_logic(self, data, *args, **kwargs):
        return FloatDataType(sum(item.data for item in data.data))


class FloatCollectValueProbe(FloatProbe):
    """A probe specialized in collecting the value of FloatDataType data."""

    def _process_logic(self, data, *args, **kwargs):
        return data.data


class FloatMockDataSource(DataSource):
    """Concrete implementation of DataSource providing FloatDataType data."""

    @classmethod
    def _get_data(cls, *args, **kwargs) -> FloatDataType:
        return FloatDataType(42.0)

    @classmethod
    def output_data_type(cls):
        return FloatDataType


class FloatMockDataSink(DataSink):
    """Concrete implementation of Datasink for FloatDataType data."""

    def _send_data(self, data: BaseDataType, path: str, *args, **kwargs):
        return

    @classmethod
    def input_data_type(cls):
        return FloatDataType


# -----------------------------------------------------------------------------------
# DUMMY IMPLEMENTATIONS FOR TESTING
# -----------------------------------------------------------------------------------


class DummyContext(ContextType):
    """
    Minimal stand-in for a context type.
    """

    pass


class FloatDataSource(DataSource):
    """
    Concrete implementation of DataSource
    providing FloatDataType data.
    """

    @classmethod
    def _get_data(cls, *args, **kwargs) -> FloatDataType:
        # Return a fixed FloatDataType for testing
        return FloatDataType(123.0)

    @classmethod
    def output_data_type(cls):
        # Return the type of data we are providing
        return FloatDataType


class FloatPayloadSource(PayloadSource):
    """
    Concrete implementation of PayloadSource
    providing (FloatDataType, DummyContext) as payload.
    """

    def _get_payload(self, *args, **kwargs) -> Tuple[FloatDataType, DummyContext]:
        # Return a tuple of data and context
        return (FloatDataType(456.0), DummyContext())

    @classmethod
    def output_data_type(cls):
        # Return the type of data in the payload
        return FloatDataType

    @classmethod
    def _injected_context_keys(cls):
        # Return the keys of the context injected by the source
        return []


class FloatDataSink(DataSink[FloatDataType]):
    """
    Concrete implementation of DataSink
    accepting FloatDataType data.
    """

    def __init__(self):
        self.last_data_sent = None

    def _send_data(self, data: FloatDataType, *args, **kwargs):
        # Keep track of the last data we received
        self.last_data_sent = data

    @classmethod
    def input_data_type(cls):
        # Return the type of data we accept
        return FloatDataType


class FloatPayloadSink(PayloadSink[FloatDataType]):
    """
    Concrete implementation of PayloadSink
    accepting (FloatDataType, DummyContext).
    """

    def __init__(self):
        self.last_payload = None
        self.last_context = None

    def _send_payload(self, data: FloatDataType, context: ContextType, *args, **kwargs):
        # Store the payload for inspection
        self.last_payload = data
        self.last_context = context

    @classmethod
    def input_data_type(cls):
        # Return the type of data we accept
        return FloatDataType
