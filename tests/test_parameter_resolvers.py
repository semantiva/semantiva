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

"""Tests for parameter resolver functionality."""


from semantiva.registry.parameter_resolver_registry import (
    ParameterResolverRegistry,
    resolve_parameters,
)


class TestParameterResolvers:
    """Test parameter resolver functionality."""

    def setup_method(self):
        """Clear resolvers before each test."""
        ParameterResolverRegistry.clear()

    def test_parameter_resolvers_are_recursive(self):
        """Test that parameter resolution works recursively on nested structures."""

        def twice_resolver(value):
            if isinstance(value, str) and value.startswith("twice:"):
                v = value.split(":", 1)[1]
                return v + v
            return None

        ParameterResolverRegistry.register_resolver(twice_resolver)

        payload = {
            "a": "twice:hi",
            "b": ["twice:x", {"c": "twice:y"}],
            "d": "normal_string",
            "e": 42,
        }

        result = resolve_parameters(payload)

        expected = {
            "a": "hihi",
            "b": ["xx", {"c": "yy"}],
            "d": "normal_string",
            "e": 42,
        }

        assert result == expected

    def test_multiple_resolvers_in_order(self):
        """Test that multiple resolvers are tried in registration order."""

        def first_resolver(value):
            if isinstance(value, str) and value.startswith("first:"):
                return "first_handled"
            return None

        def second_resolver(value):
            if isinstance(value, str) and value.startswith("second:"):
                return "second_handled"
            return None

        def catch_all_resolver(value):
            if isinstance(value, str) and value.startswith("first:"):
                return "catch_all_handled"  # Should not be reached
            return None

        ParameterResolverRegistry.register_resolver(first_resolver)
        ParameterResolverRegistry.register_resolver(second_resolver)
        ParameterResolverRegistry.register_resolver(catch_all_resolver)

        test_data = {
            "first": "first:test",
            "second": "second:test",
            "unhandled": "other:test",
        }

        result = resolve_parameters(test_data)

        assert result["first"] == "first_handled"  # First resolver should handle
        assert result["second"] == "second_handled"  # Second resolver should handle
        assert result["unhandled"] == "other:test"  # Should remain unchanged

    def test_empty_resolvers(self):
        """Test that resolution works with no registered resolvers."""
        # No resolvers registered

        payload = {"a": "test:value", "b": ["item1", "item2"], "c": {"nested": "value"}}

        result = resolve_parameters(payload)

        # Should return unchanged
        assert result == payload

    def test_non_string_values_unchanged(self):
        """Test that non-string values are passed through unchanged."""

        def string_resolver(value):
            if isinstance(value, str):
                return "resolved"
            return None

        ParameterResolverRegistry.register_resolver(string_resolver)

        payload = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }

        result = resolve_parameters(payload)

        assert result["string"] == "resolved"  # String should be resolved
        assert result["int"] == 42  # Numbers unchanged
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None
        assert result["list"] == [1, 2, 3]  # List structure unchanged
        assert result["dict"] == {"key": "resolved"}  # But strings inside are resolved

    def test_complex_nested_structures(self):
        """Test resolution on deeply nested structures."""

        def prefix_resolver(value):
            if isinstance(value, str) and value.startswith("resolve:"):
                return value.replace("resolve:", "resolved_")
            return None

        ParameterResolverRegistry.register_resolver(prefix_resolver)

        payload = {
            "level1": {
                "level2": {
                    "level3": ["resolve:deep", "normal"],
                    "other": "resolve:another",
                },
                "array": ["resolve:item1", {"nested": "resolve:item2"}],
            }
        }

        result = resolve_parameters(payload)

        expected = {
            "level1": {
                "level2": {
                    "level3": ["resolved_deep", "normal"],
                    "other": "resolved_another",
                },
                "array": ["resolved_item1", {"nested": "resolved_item2"}],
            }
        }

        assert result == expected

    def test_resolver_registry_management(self):
        """Test resolver registry management functions."""

        def test_resolver(value):
            return None

        def builtin_resolver(value):
            return None

        # Test registration
        ParameterResolverRegistry.register_resolver(test_resolver)
        ParameterResolverRegistry.register_resolver(builtin_resolver, builtin=True)

        # Test that resolvers are tracked
        resolvers = list(ParameterResolverRegistry.resolvers())
        assert test_resolver in resolvers
        assert builtin_resolver in resolvers

        # Test builtin tracking
        builtin_names = ParameterResolverRegistry.builtin_names()
        assert "builtin_resolver" in builtin_names

        # Test clear
        ParameterResolverRegistry.clear()
        assert len(list(ParameterResolverRegistry.resolvers())) == 0
        assert len(ParameterResolverRegistry.builtin_names()) == 0
