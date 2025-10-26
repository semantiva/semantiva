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

"""CopyDataProbe utility component for pass-through inspection."""

from typing import Type

from semantiva.data_types import BaseDataType
from semantiva.data_processors.data_processors import DataProbe


class CopyDataProbe(DataProbe):
    """Returns input data unchanged."""

    @classmethod
    def input_data_type(cls) -> Type[BaseDataType]:
        """Accept any BaseDataType subclass as input."""
        return BaseDataType

    def _process_logic(self, data: BaseDataType) -> BaseDataType:
        """Return the input data unchanged (identity function).

        Args:
            data: The input data to pass through.

        Returns:
            The same data object (preserves identity).
        """
        return data
