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

from semantiva.registry.class_registry import ClassRegistry


@pytest.fixture
def reset_registry(monkeypatch):
    monkeypatch.setattr(ClassRegistry, "_custom_resolvers", [])
    monkeypatch.setattr(ClassRegistry, "_param_resolvers", [])
    monkeypatch.setattr(ClassRegistry, "_builtin_resolver_names", set())
    monkeypatch.setattr(ClassRegistry, "_initialized_defaults", False)
    yield


def test_initialize_default_modules_keeps_user_resolvers(reset_registry):
    def custom_resolver(name: str):
        return None

    def param_resolver(value):
        return None

    ClassRegistry.register_resolver(custom_resolver)
    ClassRegistry.register_param_resolver(param_resolver)

    ClassRegistry.initialize_default_modules()
    ClassRegistry.initialize_default_modules()

    assert custom_resolver in ClassRegistry._custom_resolvers
    assert param_resolver in ClassRegistry._param_resolvers
    assert ClassRegistry._custom_resolvers.count(custom_resolver) == 1
    assert ClassRegistry._param_resolvers.count(param_resolver) == 1
