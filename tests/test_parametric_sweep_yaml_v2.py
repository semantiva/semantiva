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

from pathlib import Path

import pytest
import yaml

from semantiva.data_types.data_types import NoDataType
from semantiva.pipeline.payload import Payload
from semantiva.pipeline.pipeline import Pipeline


def _load_pipeline_from(path: Path) -> Pipeline:
    cfg = yaml.safe_load(path.read_text())
    return Pipeline(cfg["pipeline"]["nodes"])


def test_yaml_datasource_file(empty_context):
    p = Path(__file__).parent / "data" / "sweep_v2_datasource.yaml"
    pipeline = _load_pipeline_from(p)
    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data, ctx = payload.data, payload.context
    assert [x.data for x in data] == [-2.0, 1.0, 4.0]
    assert len(ctx.get_value("t_values")) == 3


def test_yaml_operation_file(empty_context):
    p = Path(__file__).parent / "data" / "sweep_v2_operation.yaml"
    pipeline = _load_pipeline_from(p)
    payload = pipeline.process(Payload(NoDataType(), empty_context))
    data = payload.data
    assert [x.data for x in data] == [2.0, 4.0, 6.0]


def test_yaml_probe_file(empty_context):
    p = Path(__file__).parent / "data" / "sweep_v2_probe.yaml"
    pipeline = _load_pipeline_from(p)
    payload = pipeline.process(Payload(NoDataType(), empty_context))
    assert payload.context.get_value("probe_values") == [10.0, 10.0, 10.0]


def test_yaml_errors(empty_context, tmp_path):
    bad = """
pipeline:
  nodes:
    - processor: FloatValueDataSource
      derive:
        parameter_sweep:
          parameters:
            value: "1.0 * t"
          variables: {}
          collection: FloatDataCollection
"""
    p = tmp_path / "bad.yaml"
    p.write_text(bad)
    with pytest.raises(ValueError):
        Pipeline(yaml.safe_load(p.read_text())["pipeline"]["nodes"])

    bad2 = """
pipeline:
  nodes:
    - processor: FloatCollectValueProbe
      derive:
        parameter_sweep:
          parameters: {}
          variables:
            n: { lo: 1, hi: 2, steps: 2 }
          collection: FloatDataCollection
"""
    p2 = tmp_path / "bad2.yaml"
    p2.write_text(bad2)
    with pytest.raises(ValueError):
        Pipeline(yaml.safe_load(p2.read_text())["pipeline"]["nodes"])
