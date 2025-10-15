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

from semantiva.registry import (
    NameResolverRegistry,
    ParameterResolverRegistry,
    ProcessorRegistry,
    resolve_parameters,
    resolve_symbol,
)
from semantiva.registry.builtin_resolvers import register_builtin_resolvers


@pytest.fixture(autouse=True)
def reset_registries():
    ProcessorRegistry.clear()
    NameResolverRegistry.clear()
    ParameterResolverRegistry.clear()
    register_builtin_resolvers()
    yield
    ProcessorRegistry.clear()
    NameResolverRegistry.clear()
    ParameterResolverRegistry.clear()
    register_builtin_resolvers()


def test_register_modules_and_resolve():
    ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])
    cls = resolve_symbol("FloatMultiplyOperation")
    assert cls.__name__ == "FloatMultiplyOperation"


def test_builtin_resolvers_create_dynamic_classes():
    ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])
    rename_cls = resolve_symbol("rename:alpha.beta:features.beta")
    delete_cls = resolve_symbol("delete:temp.key")
    slicer_cls = resolve_symbol("slice:FloatMultiplyOperation:FloatDataCollection")

    assert rename_cls.__name__.startswith("Rename_")
    assert delete_cls.__name__.startswith("Delete_")
    assert "Slicer" in slicer_cls.__name__


def test_template_resolver_validates_templates():
    ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])
    cls = resolve_symbol("template:'exp_{subject}_{run}.png':filename")
    processor = cls()
    with pytest.raises(KeyError):
        processor._process_logic()  # type: ignore[attr-defined]


def test_parameter_resolver_invoked_recursively():
    ProcessorRegistry.register_modules(["semantiva.workflows.fitting_model"])

    params = {
        "model": "model:FittingModel:v0=1",
        "nested": ["model:FittingModel:v0=2"],
    }
    resolved = resolve_parameters(params)
    assert resolved["model"].class_path.endswith("FittingModel")
    assert resolved["nested"][0].class_path.endswith("FittingModel")
