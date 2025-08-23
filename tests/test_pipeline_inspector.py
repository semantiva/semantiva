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

import yaml
from semantiva import Pipeline, Payload
from semantiva.inspection import build_pipeline_inspection
from semantiva.context_processors import ContextType


def test_inspection_with_slicer_prefix():
    """Ensure inspection resolves processors using the ``slicer:`` prefix."""

    yaml_config = """
pipeline:
  nodes:
    - processor: "slicer:FloatMultiplyOperation:FloatDataCollection"
      parameters:
        factor: 2
"""

    node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]

    pipeline = Pipeline(node_configs)
    from semantiva.examples.test_utils import FloatDataCollection, FloatDataType

    payload = Payload(FloatDataCollection([FloatDataType(1.0)]), ContextType())
    pipeline.process(payload)
    assert (
        pipeline.nodes[0].processor.__class__.__name__
        == "SlicerForFloatMultiplyOperation"
    )

    inspection = build_pipeline_inspection(pipeline.pipeline_configuration)
    assert inspection.nodes[0].processor_class == "SlicerForFloatMultiplyOperation"
