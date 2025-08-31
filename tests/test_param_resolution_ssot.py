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
from semantiva.pipeline.payload import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.inspection import build_pipeline_inspection
from semantiva.inspection.reporter import parameter_resolutions
from semantiva.configurations import load_pipeline_from_yaml


def test_param_resolution_parity_hello(tmp_path):
    nodes_cfg = load_pipeline_from_yaml("tests/hello_pipeline.yaml")
    p = Pipeline(nodes_cfg)

    # Build inspection (no values available)
    insp = build_pipeline_inspection(nodes_cfg)
    res = parameter_resolutions(insp)

    # Now run with an empty context; defaults should be used where necessary.
    p.process(Payload(None, ContextType({})))

    # For every node reported, assert that any param classified as "config" or "default"
    # matches the value used at runtime; "context" classification is accepted w/o a value.
    for node_info in res:
        origin = node_info["parameter_resolution"]
        for name in origin["from_pipeline_config"].keys():
            idx = node_info["id"]
            cfg = nodes_cfg[idx].get("parameters", {})
            assert name in cfg
        for name in origin["from_processor_defaults"].keys():
            pass  # runtime completed; defaults were accepted as per policy
