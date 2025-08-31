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
Factory-generated context processor tests.

Tests dynamically created rename and delete processors via factory functions,
verifying signature introspection, actual runtime behavior, and inspection compliance.
"""

from semantiva.registry import ClassRegistry


def test_rename_factory_signature_exposes_original_key():
    cls = ClassRegistry.get_class("rename:alpha.beta:features.beta")
    names = cls.get_processing_parameter_names()
    assert "alpha.beta" in names  # parameter comes from original key


def test_delete_factory_signature_exposes_deleted_key():
    cls = ClassRegistry.get_class("delete:temp.key")
    names = cls.get_processing_parameter_names()
    assert names == ["temp.key"]  # reports the key that will be consumed/deleted


def test_rename_factory_behavior():
    cls = ClassRegistry.get_class("rename:a:b")
    proc = cls()
    from semantiva.context_processors.context_observer import _ValidatingContextObserver
    from semantiva.context_processors.context_types import ContextType

    ctx = ContextType({"a": 10})
    obs = _ValidatingContextObserver(
        context_keys=cls.get_created_keys(),
        suppressed_keys=cls.get_suppressed_keys(),
        logger=None,
    )
    obs.observer_context = ctx
    proc._set_context_observer(obs)
    proc._process_logic(**{"a": 10})
    assert ctx.get_value("b") == 10
    assert "a" not in ctx.keys()


def test_delete_factory_behavior():
    cls = ClassRegistry.get_class("delete:temp")
    proc = cls()
    from semantiva.context_processors.context_observer import _ValidatingContextObserver
    from semantiva.context_processors.context_types import ContextType

    ctx = ContextType({"temp": 42, "keep": 1})
    obs = _ValidatingContextObserver(
        context_keys=cls.get_created_keys(),
        suppressed_keys=cls.get_suppressed_keys(),
        logger=None,
    )
    obs.observer_context = ctx
    proc._set_context_observer(obs)
    proc._process_logic(**{"temp": 42})  # Pass the key value as parameter
    assert "temp" not in ctx.keys()
    assert ctx.get_value("keep") == 1  # Other keys preserved


def test_delete_factory_inspection_reports_required_key():
    """Test that delete operations are properly detected as requiring context keys."""
    from semantiva.inspection import build_pipeline_inspection
    from semantiva.inspection.reporter import parameter_resolutions

    cfg = [{"processor": "delete:mykey"}]
    insp = build_pipeline_inspection(cfg)
    res = parameter_resolutions(insp)

    # The delete operation should require 'mykey' from context
    assert "mykey" in insp.required_context_keys
    assert "mykey" in res[0]["parameter_resolution"]["from_context"]
