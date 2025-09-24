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

"""Tests for current_profile functionality."""

import pytest

from semantiva.registry.bootstrap import current_profile, apply_profile, RegistryProfile
from semantiva.registry.processor_registry import ProcessorRegistry


@pytest.mark.no_auto_examples
class TestCurrentProfile:
    """Test the current_profile() functionality."""

    def setup_method(self):
        """Clear registry before each test."""
        ProcessorRegistry.clear()

    def test_current_profile_returns_module_history(self):
        """Test that current_profile() returns registered modules."""
        # Register some modules
        test_modules = [
            "semantiva.context_processors.context_processors",
            "semantiva.workflows.fitting_model",
        ]
        ProcessorRegistry.register_modules(test_modules)

        # Get current profile
        profile = current_profile()

        # Should return modules in sorted order
        assert profile.modules == sorted(test_modules)

    def test_current_profile_paths_empty(self):
        """Test that current_profile() returns empty paths."""
        # Register some modules
        ProcessorRegistry.register_modules(["semantiva.workflows.fitting_model"])

        profile = current_profile()

        # Paths should be empty as per the spec
        assert profile.paths == []

    def test_current_profile_load_defaults_true(self):
        """Test that current_profile() sets load_defaults to True."""
        profile = current_profile()
        assert profile.load_defaults is True

    def test_current_profile_extensions_empty(self):
        """Test that current_profile() returns empty extensions list."""
        profile = current_profile()
        # Extensions tracking is not currently implemented, should be empty
        assert profile.extensions == []

    def test_current_profile_with_multiple_registrations(self):
        """Test current_profile() with multiple module registrations."""
        # Register modules in multiple calls
        ProcessorRegistry.register_modules(["semantiva.workflows.fitting_model"])
        ProcessorRegistry.register_modules(
            ["semantiva.context_processors.context_processors"]
        )
        ProcessorRegistry.register_modules(
            ["semantiva.workflows.fitting_model"]
        )  # Duplicate

        profile = current_profile()

        # Should contain all registered modules (including duplicates from history)
        # Note: current_profile() sorts modules from history, so duplicates will be present
        module_history = list(ProcessorRegistry.module_history())
        assert sorted(profile.modules) == sorted(module_history)

    def test_profile_serialization(self):
        """Test that profile can be serialized and has proper structure."""
        ProcessorRegistry.register_modules(["semantiva.workflows.fitting_model"])

        profile = current_profile()

        # Test as_dict method
        profile_dict = profile.as_dict()
        assert isinstance(profile_dict, dict)
        assert "load_defaults" in profile_dict
        assert "modules" in profile_dict
        assert "paths" in profile_dict
        assert "extensions" in profile_dict

        assert profile_dict["load_defaults"] is True
        assert isinstance(profile_dict["modules"], list)
        assert isinstance(profile_dict["paths"], list)
        assert isinstance(profile_dict["extensions"], list)

        # Paths should be empty
        assert profile_dict["paths"] == []

    def test_profile_fingerprint(self):
        """Test that profile generates consistent fingerprints."""
        ProcessorRegistry.register_modules(["semantiva.workflows.fitting_model"])

        profile1 = current_profile()
        profile2 = current_profile()

        # Same state should produce same fingerprint
        assert profile1.fingerprint() == profile2.fingerprint()

        # Different state should produce different fingerprint
        ProcessorRegistry.register_modules(
            ["semantiva.context_processors.context_processors"]
        )
        profile3 = current_profile()

        assert profile1.fingerprint() != profile3.fingerprint()

    def test_apply_profile_modules(self):
        """Test that apply_profile correctly applies module registrations."""
        # Create a profile with specific modules
        test_modules = ["semantiva.workflows.fitting_model"]
        profile = RegistryProfile(
            load_defaults=False,  # Don't load defaults for this test
            modules=test_modules,
            paths=[],
            extensions=[],
        )

        # Clear registry and apply profile
        ProcessorRegistry.clear()
        apply_profile(profile)

        # Verify modules were registered
        registered_modules = ProcessorRegistry.module_history()
        assert "semantiva.workflows.fitting_model" in registered_modules

    def test_empty_registry_profile(self):
        """Test current_profile() with empty registry."""
        # Ensure registry is clear
        ProcessorRegistry.clear()

        profile = current_profile()

        assert profile.modules == []
        assert profile.paths == []
        assert profile.load_defaults is True
        assert profile.extensions == []
