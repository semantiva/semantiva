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

from semantiva.inspection import (
    build_pipeline_inspection,
    extended_report,
    summary_report,
)
from semantiva.metadata.semantic_id import compute_node_semantic_id


_SWEEP_PIPELINE_YAML = """
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
    - processor: FloatMultiplyOperation
      parameters:
        {}
"""


def _build_inspection():
    # Ensure example processors are available even if registry was cleared.
    from semantiva.examples.extension import SemantivaExamplesExtension

    SemantivaExamplesExtension().register()
    cfg = yaml.safe_load(_SWEEP_PIPELINE_YAML)
    return build_pipeline_inspection(cfg["pipeline"]["nodes"])


def test_inspection_required_keys_and_created_and_external(empty_context):
    insp = _build_inspection()

    node0 = insp.nodes[0]
    assert "vals" in node0.context_params
    assert "vals" in node0.required_external_parameters
    assert any(k.endswith("_values") for k in node0.created_keys)
    assert node0.derived_summary is not None
    assert "parameter_sweep" in node0.derived_summary
    assert node0.preprocessor_metadata is not None
    assert node0.preprocessor_metadata["type"] == "derive.parameter_sweep"
    param_meta = node0.preprocessor_metadata["param_expressions"]["value"]
    assert "expr" not in param_meta
    assert node0.preprocessor_view is not None
    assert node0.preprocessor_view["param_expressions"]["value"]["expr"] == "vals"

    node1 = insp.nodes[1]
    req_ext = getattr(node1, "required_external_parameters", [])
    assert "factor" in req_ext
    assert "factor" in insp.required_context_keys


def test_summary_and_extended_reports_include_derived_preprocessor():
    insp = _build_inspection()

    summary = summary_report(insp)
    assert "Derived preprocessor:" in summary
    assert "expr:" not in summary

    extended = extended_report(insp)
    assert "Derived preprocessor:" in extended
    assert "expr: vals" in extended
    assert "sig:" in extended


def test_compute_node_semantic_id_ignores_preprocessor_view():
    insp = _build_inspection()
    node0 = insp.nodes[0]
    base_meta = node0.preprocessor_metadata
    assert base_meta is not None
    view = node0.preprocessor_view
    assert view is not None

    id_without_view = compute_node_semantic_id(base_meta)
    meta_with_view = dict(base_meta)
    meta_with_view["preprocessor_view"] = view
    id_with_view = compute_node_semantic_id(meta_with_view)

    assert id_without_view == id_with_view
