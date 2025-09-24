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

from semantiva.registry import ProcessorRegistry, resolve_symbol
from semantiva.registry.bootstrap import RegistryProfile, apply_profile, current_profile


@pytest.fixture(autouse=True)
def reset_processor_registry():
    ProcessorRegistry.clear()
    yield
    ProcessorRegistry.clear()


def test_profile_fingerprint_stable_after_apply():
    apply_profile(RegistryProfile())
    profile = current_profile()
    fingerprint = profile.fingerprint()
    apply_profile(profile)
    assert current_profile().fingerprint() == fingerprint


def test_apply_profile_registers_modules_once(monkeypatch):
    profile = RegistryProfile(
        load_defaults=False, modules=["semantiva.examples.test_utils"]
    )
    apply_profile(profile)
    apply_profile(profile)
    cls = resolve_symbol("FloatMultiplyOperation")
    assert cls.__name__ == "FloatMultiplyOperation"
