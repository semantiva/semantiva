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

from semantiva.pipeline import Pipeline
from semantiva.examples.test_utils import FloatDataType

# Pipeline configuration matching test_pipeline_defaults.yaml
pipeline_config = [
    {"processor": "FloatValueDataSource"},
    {"processor": "FloatMultiplyOperationWithDefault", "parameters": {"factor": 2.5}},
    {"processor": "FloatMultiplyOperationWithDefault"},
    {"processor": "FloatCollectValueProbe", "context_keyword": "factor"},
    {"processor": "FloatMultiplyOperationWithDefault"},
    {"processor": "rename:factor:dead_factor"},
    {"processor": "FloatPayloadSink"},
]


def test_pipeline_defaults_execution():
    pipeline = Pipeline(pipeline_config)
    # Initial data is produced by FloatValueDataSource: 42.0
    # Node 2: 42.0 * 2.5 = 105.0
    # Node 3: 105.0 * 2.0 (default) = 210.0
    # Node 4: factor = 210.0 injected into context
    # Node 5: 210.0 * 210.0 (factor from context) = 44100.0
    # Node 6: context key 'factor' renamed to 'dead_factor'
    # Node 7: sink (no-op)
    payload = pipeline.process()
    # The final data should be 44100.0
    assert isinstance(payload.data, FloatDataType)
    assert payload.data.data == 44100.0
    # The context should have 'dead_factor' with value 210.0, and no 'factor'
    assert "dead_factor" in payload.context.keys()
    assert payload.context.get_value("dead_factor") == 210.0
    assert "factor" not in payload.context.keys()
