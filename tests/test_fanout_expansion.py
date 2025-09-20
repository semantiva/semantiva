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

import json

import pytest

from semantiva.configurations.schema import FanoutSpec
from semantiva.execution.fanout import expand_fanout
from semantiva.exceptions.pipeline_exceptions import PipelineConfigurationError


def test_single_param_expansion_order_and_values():
    spec = FanoutSpec(param="value", values=[3, 5, 9])
    runs, meta = expand_fanout(spec)
    assert runs == [{"value": 3}, {"value": 5}, {"value": 9}]
    assert meta["mode"] == "single"


def test_multi_zip_requires_equal_lengths():
    spec = FanoutSpec(multi={"value": [1, 2], "factor": [2]})
    with pytest.raises(PipelineConfigurationError):
        expand_fanout(spec)


def test_multi_zip_expands_deterministically():
    spec = FanoutSpec(multi={"value": [3, 5, 9], "factor": [2, 3, 5]})
    runs, meta = expand_fanout(spec)
    assert runs[0] == {"value": 3, "factor": 2}
    assert runs[1] == {"value": 5, "factor": 3}
    assert runs[2] == {"value": 9, "factor": 5}
    assert meta["mode"] == "multi_zip"


def test_single_param_values_file(tmp_path):
    values_path = tmp_path / "values.json"
    values_path.write_text(json.dumps([1, 2, 3]))
    spec = FanoutSpec(param="value", values_file=values_path.name)
    runs, meta = expand_fanout(spec, cwd=tmp_path)
    assert [entry["value"] for entry in runs] == [1, 2, 3]
    assert meta["source_file"] == values_path.name
    assert "source_sha256" in meta
