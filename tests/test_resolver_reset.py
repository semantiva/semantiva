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

"""Tests for built-in resolver reset functionality."""


from semantiva.registry.name_resolver_registry import NameResolverRegistry
from semantiva.registry.builtin_resolvers import reset_to_builtins


class TestResolverReset:
    """Test the reset_to_builtins() functionality."""

    def test_reset_to_builtins_restores_built_ins(self):
        """Test that reset_to_builtins() restores built-in resolvers after clear."""
        # First, verify we have built-in resolvers
        initial_resolvers = set(NameResolverRegistry.all_resolvers().keys())
        assert "rename:" in initial_resolvers
        assert "delete:" in initial_resolvers
        assert "template:" in initial_resolvers
        assert "slice:" in initial_resolvers

        # Clear all resolvers
        NameResolverRegistry.clear()
        assert len(NameResolverRegistry.all_resolvers()) == 0

        # Reset to built-ins
        reset_to_builtins()

        # Verify built-ins are restored
        restored_resolvers = set(NameResolverRegistry.all_resolvers().keys())
        assert restored_resolvers == initial_resolvers
        assert "rename:" in restored_resolvers
        assert "delete:" in restored_resolvers
        assert "template:" in restored_resolvers
        assert "slice:" in restored_resolvers

    def test_reset_to_builtins_removes_custom_resolvers(self):
        """Test that reset_to_builtins() removes any custom resolvers."""

        # Add a custom resolver
        def custom_resolver(value):
            return None

        NameResolverRegistry.register_resolver("custom:", custom_resolver)

        # Verify custom resolver is present
        resolvers = NameResolverRegistry.all_resolvers()
        assert "custom:" in resolvers

        # Reset to built-ins
        reset_to_builtins()

        # Verify custom resolver is gone, but built-ins remain
        resolvers = NameResolverRegistry.all_resolvers()
        assert "custom:" not in resolvers
        assert "rename:" in resolvers  # Built-in should still be there

    def test_reset_to_builtins_idempotent(self):
        """Test that reset_to_builtins() can be called multiple times safely."""
        # Call reset multiple times
        reset_to_builtins()
        resolvers_after_first = dict(NameResolverRegistry.all_resolvers())

        reset_to_builtins()
        resolvers_after_second = dict(NameResolverRegistry.all_resolvers())

        # Should be identical
        assert resolvers_after_first.keys() == resolvers_after_second.keys()

    def test_built_in_resolvers_functionality_after_reset(self):
        """Test that built-in resolvers work correctly after reset."""
        # Clear and reset
        NameResolverRegistry.clear()
        reset_to_builtins()

        # Test that built-in resolvers actually work
        # Test the template resolver
        result = NameResolverRegistry.resolve('template:"test_{value}":output')
        assert result is not None  # Should return a processor class

        # The exact behavior depends on the resolver implementation,
        # but it should not be None if the resolver is working
        assert callable(result)  # Should be a class/callable
