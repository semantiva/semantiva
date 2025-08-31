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
Integration tests for context processor pipelines.

Tests multi-step context transformations using factory-generated processors,
verifying actual state changes rather than just pipeline completion.
"""

from semantiva.pipeline import Pipeline
from semantiva.pipeline.payload import Payload
from semantiva.context_processors.context_types import ContextType


def test_rename_then_delete_pipeline():
    p = Pipeline(
        [
            {"processor": "rename:src:dst"},
            {"processor": "delete:dst"},
        ]
    )
    out = p.process(Payload(None, ContextType({"src": 7})))
    # Verify both transformations actually happened
    assert "dst" not in out.context.keys()
    assert "src" not in out.context.keys()
    # Ensure context is empty after the transformations
    assert len(out.context.keys()) == 0
