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

"""End-to-end tests for parametric sweep v2 YAML contract."""

from __future__ import annotations

import yaml

from semantiva.pipeline import Pipeline, Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.examples.test_utils import FloatDataCollection, FloatDataType
from semantiva.registry import ProcessorRegistry


def _collect_values(collection: FloatDataCollection) -> list[float]:
    return [item.data for item in collection]


class TestRegistrySetup:
    def setup_method(self) -> None:
        ProcessorRegistry.clear()
        ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])

    def teardown_method(self) -> None:
        ProcessorRegistry.clear()

    def test_datasource_sweep_executes_and_updates_context(self) -> None:
        yaml_config = """
        pipeline:
          nodes:
            - processor: FloatValueDataSource
              derive:
                parameter_sweep:
                  parameters:
                    value: "2.0 * t"
                  variables:
                    t: { lo: -1.0, hi: 2.0, steps: 3 }
                  collection: FloatDataCollection
        """

        node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]
        pipeline = Pipeline(node_configs)

        payload = pipeline.process(Payload(NoDataType(), ContextType()))

        assert isinstance(payload.data, FloatDataCollection)
        assert _collect_values(payload.data) == [-2.0, 1.0, 4.0]

        context = payload.context
        assert context.get_value("t_values") == [-1.0, 0.5, 2.0]

    def test_dataoperation_sweep_generates_collection(self) -> None:
        yaml_config = """
        pipeline:
          nodes:
            - processor: "FloatValueDataSource"
              parameters:
                value: 2.0
            - processor: FloatMultiplyOperation
              derive:
                parameter_sweep:
                  parameters:
                    factor: "factor"
                  variables:
                    factor: { values: [1.0, 2.0, 3.0] }
                  collection: FloatDataCollection
        """

        node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]
        pipeline = Pipeline(node_configs)

        payload = pipeline.process(Payload(NoDataType(), ContextType()))
        assert isinstance(payload.data, FloatDataCollection)
        assert _collect_values(payload.data) == [2.0, 4.0, 6.0]
        assert payload.context.get_value("factor_values") == [1.0, 2.0, 3.0]

    def test_dataoperation_sweep_uses_pipeline_parameters_for_missing_args(
        self,
    ) -> None:
        yaml_config = """
        pipeline:
          nodes:
            - processor: "FloatValueDataSource"
              parameters:
                value: 2.0
            - processor: FloatMultiplyOperation
              derive:
                parameter_sweep:
                  parameters: {}
                  variables:
                    placeholder: { values: [0] }
                  collection: FloatDataCollection
              parameters:
                factor: 5.0
        """

        node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]
        pipeline = Pipeline(node_configs)

        payload = pipeline.process(Payload(NoDataType(), ContextType()))
        assert isinstance(payload.data, FloatDataCollection)
        assert _collect_values(payload.data) == [10.0]
        assert payload.context.get_value("placeholder_values") == [0]

    def test_dataprobe_sweep_collects_results_and_passes_through(self) -> None:
        yaml_config = """
        pipeline:
          nodes:
            - processor: "FloatValueDataSource"
              parameters:
                value: 10.0
            - processor: FloatCollectValueProbe
              derive:
                parameter_sweep:
                  parameters: {}
                  variables:
                    step: { values: [0, 1, 2] }
              context_key: "probe_values"
        """

        node_configs = yaml.safe_load(yaml_config)["pipeline"]["nodes"]
        pipeline = Pipeline(node_configs)

        payload = pipeline.process(Payload(NoDataType(), ContextType()))

        assert isinstance(payload.data, FloatDataType)
        assert payload.data.data == 10.0

        context = payload.context
        assert context.get_value("probe_values") == [10.0, 10.0, 10.0]
