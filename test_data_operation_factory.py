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
"""Test inline creation of a data operation using OperationTopologyFactory."""

from typing import TYPE_CHECKING

from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import BaseDataType
from semantiva.data_processors import DataOperation, OperationTopologyFactory
from semantiva.pipeline import Pipeline, Payload


class StringLiteralDataType(BaseDataType):
    """Simple data type wrapping a Python string."""

    def __init__(self, data: str):
        super().__init__(data)

    def validate(self, data: str) -> bool:
        assert isinstance(data, str), "Data must be a string"
        return True


if TYPE_CHECKING:

    class HelloOperation(DataOperation):
        @classmethod
        def input_data_type(cls) -> type[StringLiteralDataType]: ...

        @classmethod
        def output_data_type(cls) -> type[StringLiteralDataType]: ...

        def _process_logic(
            self, data: StringLiteralDataType
        ) -> StringLiteralDataType: ...

else:

    def _hello_process_logic(
        self, data: StringLiteralDataType
    ) -> StringLiteralDataType:
        return StringLiteralDataType(f"Hello, {data.data}")

    HelloOperation = OperationTopologyFactory.create_data_operation(
        input_type=StringLiteralDataType,
        output_type=StringLiteralDataType,
        class_name="HelloOperation",
        _process_logic=_hello_process_logic,
    )


node_configurations = [
    {
        "processor": HelloOperation,
        "parameters": {},
    }
]


def test_string_specialization() -> None:
    pipeline = Pipeline(node_configurations)
    payload = pipeline.process(
        Payload(StringLiteralDataType("World!"), ContextType({}))
    )
    assert payload.data.data == "Hello, World!"
