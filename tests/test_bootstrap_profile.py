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

from semantiva.registry.bootstrap import RegistryProfile, apply_profile, current_profile
from semantiva.registry.class_registry import ClassRegistry


@pytest.fixture(autouse=True)
def snapshot_registry():
    custom = list(ClassRegistry._custom_resolvers)
    params = list(ClassRegistry._param_resolvers)
    modules = set(ClassRegistry._registered_modules)
    paths = set(ClassRegistry._registered_paths)
    builtin = set(ClassRegistry._builtin_resolver_names)
    initialized = ClassRegistry._initialized_defaults
    yield
    ClassRegistry._custom_resolvers = list(custom)
    ClassRegistry._param_resolvers = list(params)
    ClassRegistry._registered_modules = set(modules)
    ClassRegistry._registered_paths = set(paths)
    ClassRegistry._builtin_resolver_names = set(builtin)
    ClassRegistry._initialized_defaults = initialized


def test_profile_fingerprint_stable_after_apply():
    profile = current_profile()
    fingerprint = profile.fingerprint()
    apply_profile(profile)
    assert current_profile().fingerprint() == fingerprint


def test_apply_profile_registers_modules_once(monkeypatch):
    monkeypatch.setattr(ClassRegistry, "_registered_modules", set())
    profile = RegistryProfile(
        load_defaults=False, modules=["semantiva.examples.test_utils"]
    )
    apply_profile(profile)
    apply_profile(profile)
    assert "semantiva.examples.test_utils" in ClassRegistry.get_registered_modules()
