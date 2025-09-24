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

from semantiva.registry import NameResolverRegistry, ParameterResolverRegistry
from semantiva.registry.builtin_resolvers import register_builtin_resolvers


@pytest.fixture(autouse=True)
def clear_registries():
    NameResolverRegistry.clear()
    ParameterResolverRegistry.clear()
    register_builtin_resolvers()
    yield
    NameResolverRegistry.clear()
    ParameterResolverRegistry.clear()
    register_builtin_resolvers()


def test_builtin_registration_keeps_custom_resolvers():
    def custom_name_resolver(value: str):
        return None

    def custom_param_resolver(value):
        return None

    NameResolverRegistry.register_resolver("custom:", custom_name_resolver)
    ParameterResolverRegistry.register_resolver(custom_param_resolver)

    before_params = list(ParameterResolverRegistry.resolvers())
    register_builtin_resolvers()
    after_params = list(ParameterResolverRegistry.resolvers())

    assert NameResolverRegistry.all_resolvers()["custom:"] is custom_name_resolver
    assert custom_param_resolver in after_params
    assert len(after_params) == len(before_params)  # no duplicates on re-register
