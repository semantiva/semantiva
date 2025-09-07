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

"""
Test case to demonstrate that our contract validation catches non-stateless data_io components.
"""

from semantiva.data_types import NoDataType
from semantiva.contracts.expectations import validate_components


def test_stateless_contracts_detect_bad_classes() -> None:
    """Validate that intentionally-bad stateless components are flagged by contracts."""

    class BadDataSource:
        """Example of BAD implementation: not stateless (plain class, not registered)"""

        @classmethod
        def get_metadata(cls):
            return {
                "class_name": "BadDataSource",
                "docstring": "Bad data source for tests",
                "component_type": "DataSource",
            }

        def _get_data(self):  # Missing @classmethod - should trigger SVA005
            return NoDataType()

        @classmethod
        def output_data_type(cls):
            return NoDataType

    class BadDataSink:
        """Example of BAD implementation: not stateless (plain class)"""

        @classmethod
        def get_metadata(cls):
            return {
                "class_name": "BadDataSink",
                "docstring": "Bad data sink for tests",
                "component_type": "DataSink",
            }

        def _send_data(self, data):  # Missing @classmethod - should trigger SVA009
            pass

        @classmethod
        def input_data_type(cls):
            return NoDataType

    class BadPayloadSource:
        """Example of BAD implementation: not stateless (plain class)"""

        @classmethod
        def get_metadata(cls):
            return {
                "class_name": "BadPayloadSource",
                "docstring": "Bad payload source for tests",
                "component_type": "PayloadSource",
            }

        def _get_payload(self):  # Missing @classmethod - should trigger SVA007
            return None

        @classmethod
        def output_data_type(cls):
            return NoDataType

        @classmethod
        def _injected_context_keys(cls):
            return []

    class BadPayloadSink:
        """Example of BAD implementation: not stateless (plain class)"""

        @classmethod
        def get_metadata(cls):
            return {
                "class_name": "BadPayloadSink",
                "docstring": "Bad payload sink for tests",
                "component_type": "PayloadSink",
            }

        def _send_payload(
            self, payload
        ):  # Missing @classmethod - should trigger SVA011
            pass

        @classmethod
        def input_data_type(cls):
            return NoDataType

    diags = validate_components(
        [BadDataSource, BadDataSink, BadPayloadSource, BadPayloadSink]
    )
    codes = {d.code for d in diags}

    # Expect the specific stateless-related errors
    assert (
        "SVA005" in codes or "SVA009" in codes or "SVA007" in codes or "SVA011" in codes
    )
