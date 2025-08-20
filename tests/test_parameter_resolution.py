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

from semantiva.inspection import (
    build_pipeline_inspection,
    parameter_resolutions,
)
from semantiva.examples.test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
)


def test_get_node_parameter_resolutions_empty_pipeline():
    node_configuration = []
    inspection = build_pipeline_inspection(node_configuration)
    resolutions = parameter_resolutions(inspection)
    assert isinstance(resolutions, list)
    assert len(resolutions) == 0


def test_get_node_parameter_resolutions_complex_key_origin():
    """Test parameter resolution with complex key origins."""
    # Create a pipeline with multiple sources for the same key
    node_configuration = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": FloatMultiplyOperation},
        {"processor": "rename:factor:renamed_factor"},  # factor -> renamed_factor
        {
            "processor": FloatCollectValueProbe,
            "context_keyword": "factor",
        },  # Creates factor again
        {"processor": FloatMultiplyOperation},  # Uses factor from node 4, not node 1
    ]

    inspection = build_pipeline_inspection(node_configuration)
    resolutions = parameter_resolutions(inspection)

    # Check the resolution for the second FloatMultiplyOperation
    last_multiply = resolutions[4]  # 0-indexed, fifth node
    assert "factor" in last_multiply["parameter_resolution"]["from_context"]
    # The factor should come from node 4, not from node 1
    assert (
        last_multiply["parameter_resolution"]["from_context"]["factor"]["source_idx"]
        == 4
    )
