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

"""
Layer 1: Metadata Contract Validation (Static)

Authoritative, exhaustive validation of all `_SemantivaComponent` subclasses’ metadata structures.

Coverage (must be explicitly documented as a top-level docstring inside `tests/test_metadata_contracts.py`):

1. Global invariants (all components):
   - Required keys: `class_name`, `docstring`, `component_type`.
   - `_define_metadata()` returns `dict`.
   - `get_metadata()` merges base + component-level fields (no exceptions).
2. Component category expectations (Required vs Forbidden metadata keys):
   - DataSource: required: `output_data_type`; forbidden: `input_data_type`.
   - PayloadSource: required: `output_data_type`; forbidden: `input_data_type`.
   - DataSink: required: `input_data_type`; forbidden: `output_data_type`.
   - PayloadSink: required: `input_data_type`; forbidden: `output_data_type`.
   - DataOperation: required: `input_data_type`, `output_data_type`; `parameters` present (dict/list); forbidden: none of above missing.
   - DataProbe: required: `input_data_type`; forbidden: `output_data_type`.
   - ContextProcessor (if used): may have only context-related keys; forbidden: data type keys.
   - Node wrappers (DataSourceNode, DataSinkNode, PayloadSourceNode, PayloadSinkNode, DataOperationNode, ProbeNode):
       * Required: `component_type`, `class_name`, `docstring`.
       * Delegation checks: node’s advertised input/output types (when present) must match underlying processor contract.
       * Node category forwarding rules:
         - DataSourceNode / PayloadSourceNode: must show `input_data_type = NoDataType` and required `output_data_type`.
         - DataSinkNode / PayloadSinkNode: must show `input_data_type`, and `output_data_type` must be identical to input (pass-through). (Document difference vs base IO component rule.)
         - DataOperationNode:  `input_data_type`, and `output_data_type`.
         - ProbeNode: must show input type and the output type must be identical as the input (output == input).
3. Field value rules:
   - `component_type` string matches registry key (if registered).
   - `parameters`:
     * Either dict mapping parameter names to metadata objects / infos OR "None" / {} when no parameters.
   - `injected_context_keys` must be list if present.
4. Forbidden leakage:
   - Sources must not expose internal processing-only fields (e.g., `input_data_type`).
   - Sinks must not fabricate `output_data_type`.
   - Probes must not declare output unless semantically equal to input (enforced rule).
5. Consistency cross-checks:
   - If both `input_data_type` and `output_data_type` present and component_type endswith "Sink", assert they are identical (pass-through only when allowed—nodes).
   - For operations: assert they can differ OR be equal (both allowed).
6. Documentation by validation:
   - Expectations encoded in a helper mapping (source of truth).
7. Discovery:
   - All subclasses of `_SemantivaComponent` are included automatically (excluding private abstract starters: names starting with `_` except `_SemantivaComponent` itself).
8. No output pollution (no print).
9. Optional: Provide a single “expectation dump” test (skipped by default) to assist onboarding.
"""

from __future__ import annotations

import pytest
from semantiva.core.semantiva_component import (
    _SemantivaComponent,
    get_component_registry,
)
from semantiva.logger import Logger
from semantiva.data_processors.data_processors import DataOperation, DataProbe
from semantiva.data_io.data_io import DataSource, PayloadSource
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.examples.test_utils import (
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatBasicProbe,
)

from ._metadata_expectations import (
    EXPECTATIONS,
    validate_component_metadata,
)


def _discover_components() -> set[type[_SemantivaComponent]]:
    registry = get_component_registry()
    components = {
        cls
        for classes in registry.values()
        for cls in classes
        if not (cls.__name__.startswith("_") and cls.__name__ != "_SemantivaComponent")
        and cls not in {DataOperation, DataProbe, DataSource, PayloadSource}
    }

    logger = Logger(level="ERROR", console_output=False, name="test_logger")
    node_instances = [
        _pipeline_node_factory({"processor": FloatDataSource}, logger),
        _pipeline_node_factory({"processor": FloatPayloadSource}, logger),
        _pipeline_node_factory({"processor": FloatDataSink}, logger),
        _pipeline_node_factory({"processor": FloatPayloadSink}, logger),
        _pipeline_node_factory({"processor": FloatMultiplyOperation}, logger),
        _pipeline_node_factory(
            {"processor": FloatBasicProbe, "context_keyword": "probe"}, logger
        ),
        _pipeline_node_factory({"processor": FloatBasicProbe}, logger),
    ]
    components.update(type(n) for n in node_instances)
    Logger(level="WARNING", console_output=True, name="Semantiva")
    return components


_ALL_COMPONENTS = sorted(_discover_components(), key=lambda c: c.__name__)


@pytest.mark.parametrize("component", _ALL_COMPONENTS)
def test_component_metadata_contracts(component: type[_SemantivaComponent]):
    validate_component_metadata(component)


@pytest.mark.skip(reason="Expectation table dump for onboarding")
def test_dump_expectations():
    assert EXPECTATIONS  # pragma: no cover
