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
from semantiva.data_types import BaseDataType, DataCollectionType
from semantiva.data_processors import DataOperation, DataProbe
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from semantiva.pipeline import Payload
from typing import Optional
from semantiva.logger import Logger
from semantiva.context_processors import ContextType


# Concrete implementation of BaseDataType for testing
class FloatDataType(BaseDataType[float]):
    """A simple data type that holds a float value."""

    def validate(self, data: float) -> bool:
        """Check that ``data`` is a ``float``.

        Args:
            data: Value to validate.

        Returns:
            bool: ``True`` if the value is a float.

        Raises:
            TypeError: If ``data`` is not a float.
        """
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
        """Append a FloatDataType item to the collection.

        Args:
            item (FloatDataType): The element to add to the collection.

        Raises:
            TypeError: If ``item`` is not a ``FloatDataType`` instance.
        """
        if not isinstance(item, FloatDataType):
            raise TypeError("Item must be of type FloatDataType")
        self._data.append(item)

    def __len__(self) -> int:
        return len(self._data)

    def validate(self, data):
        """Validate that all items in the collection are FloatDataType instances.

        Args:
            data (Iterable): The collection to validate.

        Raises:
            TypeError: If any element is not a ``FloatDataType`` instance.
        """
        for item in data:
            if not isinstance(item, FloatDataType):
                raise TypeError("Data must be a list of FloatDataType objects")


# Concrete implementation of DataOperation
class FloatOperation(DataOperation):
    """Base class for operations on FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        """Return the expected input data type."""
        return FloatDataType

    @classmethod
    def output_data_type(cls):
        """Return the produced output data type."""
        return FloatDataType


class FloatCollectionMergeOperation(DataOperation):
    """Base class for operations that merge FloatDataCollection data into a single FloatDataType."""

    @classmethod
    def input_data_type(cls):
        """Return the expected collection input type."""
        return FloatDataCollection

    @classmethod
    def output_data_type(cls):
        """Return the merged output data type."""
        return FloatDataType


# Concrete implementation of DataProbe
class FloatProbe(DataProbe):
    """Base class for probes that process FloatDataType data."""

    @classmethod
    def input_data_type(cls):
        """Return the expected input data type for the probe."""
        return FloatDataType


class FloatMultiplyOperation(FloatOperation):
    """Multiply FloatDataType data by a factor."""

    def _process_logic(self, data, factor: float, *args, **kwargs):
        return FloatDataType(data.data * factor)


class FloatMultiplyOperationWithDefault(FloatOperation):
    """Multiply a Float by a factor with a default value of 2.0."""

    def _process_logic(self, data, factor: float = 2.0):
        return FloatDataType(data.data * factor)


class FloatAddOperation(FloatOperation):
    """Add a constant to FloatDataType data."""

    def _process_logic(self, data, addend: float, *args, **kwargs):
        return FloatDataType(data.data + addend)


class FloatSquareOperation(FloatOperation):
    """Square the value of FloatDataType data."""

    def _process_logic(self, data, *args, **kwargs):
        return FloatDataType(data.data**2)


class FloatSqrtOperation(FloatOperation):
    """Extract the square root of FloatDataType data."""

    def _process_logic(self, data, *args, **kwargs):
        import math

        return FloatDataType(math.sqrt(abs(data.data)))


class FloatDivideOperation(FloatOperation):
    """Divide FloatDataType data by a divisor."""

    def _process_logic(self, data, divisor: float, *args, **kwargs):
        if divisor == 0:
            raise ValueError("Division by zero is not allowed")
        return FloatDataType(data.data / divisor)


class FloatBasicProbe(FloatProbe):
    """A probe that inspects a FloatDataType data and returns a dictionary with `value`, `type`, and `is_positive` and `abs_value` keys."""

    def _process_logic(self, data, *args, **kwargs):
        return {
            "value": data.data,
            "type": type(data.data).__name__,
            "is_positive": data.data > 0,
            "abs_value": abs(data.data),
        }


class FloatCollectionSumOperation(FloatCollectionMergeOperation):
    """Sum all items in a FloatDataCollection."""

    def _process_logic(self, data, *args, **kwargs):
        return FloatDataType(sum(item.data for item in data.data))


class FloatCollectValueProbe(FloatProbe):
    """A probe that collects the value of the input."""

    def _process_logic(self, data, *args, **kwargs):
        return data.data


class FloatMockDataSource(DataSource):
    """Float DataSource. Outputs a fixed FloatDataType value. Defaults to 42.0."""

    @classmethod
    def _get_data(cls, value: float = 42.0, *args, **kwargs) -> FloatDataType:
        assert isinstance(value, float), "Value must be a float"
        return FloatDataType(value)

    @classmethod
    def output_data_type(cls):
        """Return the data type produced by this source."""
        return FloatDataType


class FloatMockDataSink(DataSink):
    """A Mock Datasink for FloatDataType data that does nothing."""

    def _send_data(self, data: BaseDataType, path: str, *args, **kwargs):
        return

    @classmethod
    def input_data_type(cls):
        """Return the data type accepted by this sink."""
        return FloatDataType


# -----------------------------------------------------------------------------------
# DUMMY IMPLEMENTATIONS FOR TESTING
# -----------------------------------------------------------------------------------


class FloatDataSource(DataSource):
    """
    A DataSource that outputs 123.0 as a FloatDataType.
    """

    @classmethod
    def _get_data(cls, *args, **kwargs) -> FloatDataType:
        # Return a fixed FloatDataType for testing
        return FloatDataType(123.0)

    @classmethod
    def output_data_type(cls):
        """Return the type of data provided by the source."""
        return FloatDataType


class FloatPayloadSource(PayloadSource):
    """
    A PayloadSource for FloatDataType that provides 456.0 and an empty context as payload.
    """

    def _get_payload(self, *args, **kwargs) -> Payload:
        # Return a Payload object with data and context
        return Payload(FloatDataType(456.0), ContextType())

    @classmethod
    def output_data_type(cls):
        """Return the data type contained in the payload."""
        return FloatDataType

    @classmethod
    def _injected_context_keys(cls):
        # Return the keys of the context injected by the source
        return []


class FloatDataSink(DataSink[FloatDataType]):
    """
    A DataSink for FloatDataType that simply stores the last data sent.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)
        self.last_data_sent: Optional[FloatDataType] = None

    def _send_data(self, data: FloatDataType, *args, **kwargs):
        # Keep track of the last data we received
        self.last_data_sent = data

    @classmethod
    def input_data_type(cls):
        """Return the data type accepted by this sink."""
        return FloatDataType


class FloatTxtFileSaver(DataSink[FloatDataType]):
    """
    Saves a float value in a text file.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)

    def _send_data(self, data: FloatDataType, file_path: str, *args, **kwargs):
        """Save the float value to a text file."""
        if not isinstance(data, FloatDataType):
            raise TypeError("Data must be of type FloatDataType")

        # Save to a file named
        with open(file_path, "w") as f:
            # Let's add a new line at the end for consistency
            f.write(str(data.data) + "\n")

    @classmethod
    def input_data_type(cls):
        """Return the data type accepted by this sink."""
        return FloatDataType


class FloatPayloadSink(PayloadSink[FloatDataType]):
    """
    A PayloadSink for FloatDataType that simply stores the last payload and context received.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)
        self.last_payload: Optional[BaseDataType] = None
        self.last_context: Optional[ContextType] = None

    def _send_payload(self, payload: Payload, *args, **kwargs):
        # Store the payload for inspection
        self.last_payload = payload.data
        self.last_context = payload.context

    @classmethod
    def input_data_type(cls):
        """Return the data type accepted by this payload sink."""
        return FloatDataType
