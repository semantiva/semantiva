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

"""DataDump utility component for explicit data channel termination."""

from typing import Type

from semantiva.data_types import BaseDataType, NoDataType
from semantiva.data_processors.data_processors import DataOperation


class DataDump(DataOperation):
    """Discards input data and returns NoDataType, stopping data propagation while preserving context."""

    @classmethod
    def input_data_type(cls) -> Type[BaseDataType]:
        """Accept any BaseDataType subclass as input."""
        return BaseDataType

    @classmethod
    def output_data_type(cls) -> Type[NoDataType]:
        """Output NoDataType to signal no data."""
        return NoDataType

    def _process_logic(self, data: BaseDataType) -> NoDataType:
        """Dump the input data and return NoDataType.

        Args:
            data: The input data to be dumped (discarded).

        Returns:
            NoDataType instance indicating no data.
        """
        return NoDataType()
