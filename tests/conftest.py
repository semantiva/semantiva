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

"""Test configuration and fixtures for Semantiva."""

import pytest

from semantiva.context_processors.context_types import ContextType
from semantiva.examples.extension import SemantivaExamplesExtension
from semantiva.examples.test_utils import FloatDataType
from semantiva.registry.builtin_resolvers import reset_to_builtins
from semantiva.registry.processor_registry import ProcessorRegistry


@pytest.fixture(autouse=True)
def _ensure_builtin_resolvers():
    """Ensure built-in resolvers are available for each test.

    This fixture automatically runs before each test to guarantee that
    built-in name resolvers (rename:, delete:, template:, slice:)
    are always present, even if previous tests called clear() on the
    NameResolverRegistry.

    This is particularly important for tests that modify the registry
    state and need to ensure a clean, consistent starting point.
    """
    # Always ensure built-ins exist for each test
    reset_to_builtins()
    yield


@pytest.fixture(autouse=True, scope="function")
def _load_examples_extension(request):
    """Automatically load the examples extension for tests that need example processors."""
    # Skip if test is marked with no_auto_examples
    if "no_auto_examples" in [marker.name for marker in request.node.iter_markers()]:
        yield
        return

    from semantiva.registry import plugin_registry

    # Store original state
    original_loaded_extensions = plugin_registry._LOADED_EXTENSIONS.copy()
    original_clear = ProcessorRegistry.clear

    # Load the extension if not already loaded
    if "semantiva-examples" not in plugin_registry._LOADED_EXTENSIONS:
        extension = SemantivaExamplesExtension()
        extension.register()
        plugin_registry._LOADED_EXTENSIONS.add("semantiva-examples")

    # Create a patched clear method that preserves the extension
    @classmethod
    def patched_clear(cls):
        original_clear()
        # Always reload the extension after clearing
        extension = SemantivaExamplesExtension()
        extension.register()
        plugin_registry._LOADED_EXTENSIONS.add("semantiva-examples")

    # Apply the patch
    ProcessorRegistry.clear = patched_clear

    try:
        yield
    finally:
        # Restore original state completely
        ProcessorRegistry.clear = original_clear
        plugin_registry._LOADED_EXTENSIONS.clear()
        plugin_registry._LOADED_EXTENSIONS.update(original_loaded_extensions)
        # Don't call clear() here as it might interfere with other fixtures


@pytest.fixture()
def empty_context():
    """Provide a fresh empty context for tests."""

    return ContextType()


@pytest.fixture()
def float_data():
    """Provide a basic float data payload for operation tests."""

    return FloatDataType(2.0)
