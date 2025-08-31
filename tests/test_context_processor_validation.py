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
Validation tests for context processor observer pattern.

Tests that ValidatingContextObserver enforces declared keys for updates
and deletions, preventing unauthorized context modifications.
"""

from semantiva.context_processors.context_observer import _ValidatingContextObserver
from semantiva.context_processors.context_types import ContextType


def test_validating_observer_allows_declared_keys():
    ctx = ContextType({})
    obs = _ValidatingContextObserver(
        context_keys=["out.k"], suppressed_keys=[], logger=None
    )
    obs.observer_context = ctx
    obs.update("out.k", 42)
    assert ctx.get_value("out.k") == 42


def test_validating_observer_rejects_undeclared_key():
    ctx = ContextType({})
    obs = _ValidatingContextObserver(
        context_keys=["out.k"], suppressed_keys=[], logger=None
    )
    obs.observer_context = ctx
    try:
        obs.update("nope", 1)
    except KeyError as e:
        assert "Invalid context key 'nope'" in str(e)
    else:
        assert False, "Expected KeyError"


def test_validating_observer_allows_declared_deletion():
    ctx = ContextType({"temp": 1})
    obs = _ValidatingContextObserver(
        context_keys=[], suppressed_keys=["temp"], logger=None
    )
    obs.observer_context = ctx
    obs.delete("temp")
    assert "temp" not in ctx.keys()


def test_validating_observer_rejects_undeclared_deletion():
    ctx = ContextType({"x": 1})
    obs = _ValidatingContextObserver(
        context_keys=[], suppressed_keys=["y"], logger=None
    )
    obs.observer_context = ctx
    try:
        obs.delete("x")
    except KeyError as e:
        assert "Invalid suppressed key 'x'" in str(e)
    else:
        assert False, "Expected KeyError"
