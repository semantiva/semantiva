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

from semantiva.registry import ClassRegistry


def test_rename_factory_signature_exposes_original_key():
    cls = ClassRegistry.get_class("rename:alpha.beta:features.beta")
    names = cls.get_processing_parameter_names()
    assert "alpha.beta" in names  # parameter comes from original key


def test_delete_factory_signature_is_empty():
    cls = ClassRegistry.get_class("delete:temp.key")
    names = cls.get_processing_parameter_names()
    assert names == []  # no inputs required to delete


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
