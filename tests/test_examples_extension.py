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

"""Tests for semantiva-examples extension."""

import pytest

from semantiva.registry import ProcessorRegistry, load_extensions, resolve_symbol


@pytest.mark.no_auto_examples
class TestSemantivaExamplesExtension:
    """Test the semantiva-examples extension functionality."""

    def test_examples_extension_registration(self):
        """Test that the semantiva-examples extension registers example processors."""
        # Clear registry first
        ProcessorRegistry.clear()

        # Load the semantiva-examples extension
        load_extensions(["semantiva-examples"])

        # Verify that example processors are now available
        processor_cls = resolve_symbol("FloatValueDataSource")
        assert processor_cls is not None
        assert processor_cls.__name__ == "FloatValueDataSource"

        # Test another example processor
        processor_cls = resolve_symbol("FloatMultiplyOperation")
        assert processor_cls is not None
        assert processor_cls.__name__ == "FloatMultiplyOperation"

        # Test a probe
        processor_cls = resolve_symbol("FloatCollectValueProbe")
        assert processor_cls is not None
        assert processor_cls.__name__ == "FloatCollectValueProbe"

    def test_examples_not_available_without_extension(self):
        """Test that example processors are not available by default."""
        # Clear registry and load only defaults (without examples)
        ProcessorRegistry.clear()
        from semantiva.registry.bootstrap import DEFAULT_MODULES

        ProcessorRegistry.register_modules(DEFAULT_MODULES)

        # Verify that example processors are NOT available
        with pytest.raises(Exception):  # Should raise UnknownProcessorError or similar
            resolve_symbol("FloatValueDataSource")

    def test_extension_multiple_loads_idempotent(self):
        """Test that loading the extension multiple times is safe."""
        ProcessorRegistry.clear()

        # Load extension twice
        load_extensions(["semantiva-examples"])
        processors_after_first = len(ProcessorRegistry.all_processors())

        load_extensions(["semantiva-examples"])
        processors_after_second = len(ProcessorRegistry.all_processors())

        # Should not double-register processors
        assert processors_after_first == processors_after_second

    def test_extension_name_resolution(self):
        """Test that the extension is properly discoverable by name."""
        ProcessorRegistry.clear()

        # Test loading by exact name
        load_extensions("semantiva-examples")  # Single string instead of list

        # Verify processors are available
        processor_cls = resolve_symbol("FloatAddOperation")
        assert processor_cls is not None
        assert processor_cls.__name__ == "FloatAddOperation"
