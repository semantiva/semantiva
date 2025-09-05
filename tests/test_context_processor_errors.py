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
Error handling tests for context processors.

Tests error conditions: missing observer runtime errors, parameter
resolution failures, and observer validation errors.
"""

from semantiva.context_processors.context_processors import ContextProcessor


class BrokenCP(ContextProcessor):
    @classmethod
    def get_created_keys(cls):
        return ["x"]

    def _process_logic(self, *, v: int) -> None:
        # This should trigger the missing observer error when called directly
        self._notify_context_update("x", v)


def test_missing_observer_runtime_error():
    b = BrokenCP()
    try:
        b._process_logic(v=1)
    except RuntimeError as e:
        assert "attempted a context update without an active ContextObserver" in str(e)
    else:
        assert False


def test_parameter_resolution_keyerror_via_node(tmp_path):
    # A node wrapping a processor that requires 'v' should raise if not resolvable
    from semantiva.context_processors.context_processors import ContextProcessor
    from semantiva.pipeline.nodes._pipeline_node_factory import _PipelineNodeFactory
    from semantiva.context_processors.context_types import ContextType
    from semantiva.pipeline.payload import Payload

    class NeedV(ContextProcessor):
        def _process_logic(self, *, v: int) -> None:
            self._notify_context_update("w", v + 1)

    node = _PipelineNodeFactory.create_context_processor_wrapper_node(NeedV, {})
    try:
        node.process(Payload(None, ContextType({})))
    except KeyError as e:
        assert "Unable to resolve parameter 'v'" in str(e)
    else:
        assert False


def test_observer_validation_error():
    """Test that observer validation errors are properly raised."""
    from semantiva.context_processors.context_observer import _ValidatingContextObserver
    from semantiva.context_processors.context_types import ContextType

    ctx = ContextType({})
    obs = _ValidatingContextObserver(
        context_keys=["allowed"], suppressed_keys=[], logger=None
    )
    obs.observer_context = ctx

    try:
        obs.update("forbidden", 1)
    except KeyError as e:
        assert "Invalid context key 'forbidden'" in str(e)
    else:
        assert False, "Expected validation error"
