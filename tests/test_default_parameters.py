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

import pytest

from semantiva.context_processors.context_types import ContextType
from semantiva.pipeline import Payload
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.inspection import build_pipeline_inspection, summary_report, json_report
from semantiva import Pipeline
from semantiva.examples.test_utils import (
    FloatDataType,
    FloatMultiplyOperationWithDefault,
    FloatMultiplyOperation,
    FloatCollectValueProbe,
)


def test_runtime_fallback_to_default():
    node = _pipeline_node_factory({"processor": FloatMultiplyOperationWithDefault})
    payload = Payload(FloatDataType(3.0), ContextType())
    result = node.process(payload)
    assert result.data.data == 6.0


def test_context_overrides_default():
    node = _pipeline_node_factory({"processor": FloatMultiplyOperationWithDefault})
    payload = Payload(FloatDataType(3.0), ContextType({"factor": 4.0}))
    result = node.process(payload)
    assert result.data.data == 12.0


def test_missing_required_parameter_raises():
    node = _pipeline_node_factory({"processor": FloatMultiplyOperation})
    payload = Payload(FloatDataType(3.0), ContextType())
    with pytest.raises(KeyError):
        node.process(payload)


def test_inspection_marks_default_and_user_params():
    # Defaulted parameter
    cfg_default = [{"processor": FloatMultiplyOperationWithDefault}]
    inspection_default = build_pipeline_inspection(cfg_default)
    report_default = summary_report(inspection_default)
    assert "From processor defaults: factor=2.0" in report_default
    assert "From pipeline configuration: None" in report_default
    json_default = json_report(inspection_default)
    assert (
        json_default["nodes"][0]["parameter_resolution"]["from_processor_defaults"][
            "factor"
        ]
        == "2.0"
    )
    assert not json_default["nodes"][0]["parameter_resolution"]["from_pipeline_config"]

    # User override
    cfg_user = [
        {"processor": FloatMultiplyOperationWithDefault, "parameters": {"factor": 5.0}}
    ]
    inspection_user = build_pipeline_inspection(cfg_user)
    report_user = summary_report(inspection_user)
    assert "From pipeline configuration: factor=5.0" in report_user
    assert "From processor defaults: None" in report_user
    json_user = json_report(inspection_user)
    assert (
        json_user["nodes"][0]["parameter_resolution"]["from_pipeline_config"]["factor"]
        == "5.0"
    )
    assert not json_user["nodes"][0]["parameter_resolution"]["from_processor_defaults"]


def test_context_overrides_default_in_pipeline():
    cfg = [
        {"processor": FloatCollectValueProbe, "context_keyword": "factor"},
        {"processor": FloatMultiplyOperationWithDefault},
    ]

    pipeline = Pipeline(cfg)
    payload = Payload(FloatDataType(4.0), ContextType())
    result = pipeline.process(payload)
    assert result.data.data == 16.0

    inspection = build_pipeline_inspection(cfg)
    report = summary_report(inspection)
    assert "From processor defaults: None" in report
    assert "From context: factor (from Node 1)" in report

    data = json_report(inspection)
    node2 = data["nodes"][1]
    assert not node2["parameter_resolution"]["from_processor_defaults"]
    assert node2["parameter_resolution"]["from_context"]["factor"]["source_idx"] == 1
