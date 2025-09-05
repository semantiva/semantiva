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
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline
from semantiva.exceptions import InvalidNodeParameterError
from semantiva.registry import ClassRegistry


def test_runtime_raises_on_unknown_param(tmp_path):
    yaml = """
pipeline:
  nodes:
    - processor: FloatMultiplyOperationWithDefault
      parameters:
        factor: 2.0
        facotr: 3.0
"""
    p = tmp_path / "bad.yaml"
    p.write_text(yaml)
    ClassRegistry.register_modules(["semantiva.examples.test_utils"])
    nodes = load_pipeline_from_yaml(str(p))
    pipe = Pipeline(nodes)
    with pytest.raises(InvalidNodeParameterError) as ei:
        pipe.process()
    msg = str(ei.value)
    assert "Invalid parameters" in msg and "facotr" in msg
    assert "node_uuid=" in msg


def test_kwargs_processor_rejected_for_provenance():
    """Processors with **kwargs should be rejected for reliable provenance."""
    from semantiva.context_processors.context_processors import ContextProcessor

    class KwargsCP(ContextProcessor):
        @classmethod
        def get_created_keys(cls):
            return ["x"]

        def _process_logic(self, *, a: int = 0, **kwargs):  # kwargs not allowed
            self._notify_context_update("x", a)

    # Should raise ValueError when introspecting processor with **kwargs
    with pytest.raises(ValueError) as exc_info:
        from semantiva.pipeline._param_resolution import _allowed_param_names

        _allowed_param_names(KwargsCP)

    assert "**kwargs which is incompatible with reliable provenance tracking" in str(
        exc_info.value
    )
