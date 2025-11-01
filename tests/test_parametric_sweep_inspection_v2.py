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

from semantiva.inspection.builder import build_pipeline_inspection


def test_inspection_required_keys_and_created_and_external(empty_context):
    cfg = yaml.safe_load(
        """
pipeline:
  nodes:
    - processor: FloatValueDataSource
      derive:
        parameter_sweep:
          parameters:
            value: "vals"
          variables:
            vals: { from_context: "vals" }
          collection: FloatDataCollection
    - processor: "FloatMultiplyOperation"
      parameters:
        {}
"""
    )
    insp = build_pipeline_inspection(cfg["pipeline"]["nodes"])

    node0 = insp.nodes[0]
    assert "vals" in node0.context_params
    assert "vals" in node0.required_external_parameters
    assert any(k.endswith("_values") for k in node0.created_keys)

    node1 = insp.nodes[1]
    req_ext = getattr(node1, "required_external_parameters", [])
    assert "factor" in req_ext
    assert "factor" in insp.required_context_keys
