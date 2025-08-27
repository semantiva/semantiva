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
from typing import List
from semantiva.context_processors.context_processors import (
    ContextProcessor,
)


def _context_renamer_factory(
    original_key: str, destination_key: str
) -> type[ContextProcessor]:
    """
    Factory function that creates a ContextProcessor subclass to rename context keys.

    Args:
        original_key (str): The key to rename.
        destination_key (str): The new key name.

    Returns:
        Type[ContextProcessor]: A dynamically generated class that renames context keys,
                                  with a name of the form "Rename_<original_key>_to_<destination_key>_Operation".
    """

    def _process_logic(self, **kwargs) -> None:
        """
        Get the value for the original key from the resolved parameters,
        and updates the destination key through the context observer.
        """
        # Get the original key value from kwargs - it will be injected by parameter resolution
        value = kwargs.get(original_key)
        if value is not None:
            self._notify_context_update(destination_key, value)
            self._notify_context_deletion(original_key)
            self.logger.debug(
                f"Renamed context key '{original_key}' -> '{destination_key}'"
            )
        else:
            self.logger.warning(
                f"Key '{original_key}' not found in resolved parameters."
            )

    # Create a closure that captures both keys
    def create_process_logic_with_signature():
        # Create a function with the proper signature using a different approach
        import inspect

        # Create the function code manually with the correct signature
        def _process_logic_with_signature(self, **kwargs):
            # Extract the original key value from kwargs
            value = kwargs.get(original_key)
            if value is not None:
                self._notify_context_update(destination_key, value)
                self._notify_context_deletion(original_key)
                self.logger.debug(
                    f"Renamed context key '{original_key}' -> '{destination_key}'"
                )
            else:
                self.logger.warning(
                    f"Key '{original_key}' not found in resolved parameters."
                )

        # Create a new signature with the original_key as a parameter
        old_sig = inspect.signature(_process_logic_with_signature)
        new_params = [
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(original_key, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ]
        # Add remaining parameters
        for param in old_sig.parameters.values():
            if param.name not in ["self"]:
                new_params.append(param)

        new_sig = inspect.Signature(new_params)
        _process_logic_with_signature.__signature__ = new_sig
        _process_logic_with_signature.__name__ = "_process_logic_with_signature"
        return _process_logic_with_signature
        return _process_logic_with_signature

    _process_logic = create_process_logic_with_signature()

    def get_required_keys(cls) -> List[str]:
        """
        Return a list containing the original key, as it is required for renaming.
        """
        return [original_key]

    def get_created_keys(cls) -> List[str]:
        """
        Return a list containing the new key, which is created as a result of renaming.
        """
        return [destination_key]

    def get_suppressed_keys(cls) -> List[str]:
        """
        Return a list containing the original key, since it is suppressed after renaming.
        """
        return [original_key]

    def context_keys(cls) -> List[str]:
        """
        Return a list containing the destination key, which this processor can modify.
        """
        return [destination_key]

    # Create a dynamic class name that clearly shows the renaming transformation
    dynamic_class_name = f"Rename_{original_key}_to_{destination_key}"

    # Define the class attributes and methods in a dictionary
    class_attrs = {
        # "__name__": dynamic_class_name,
        "_process_logic": _process_logic,
        "get_required_keys": classmethod(get_required_keys),
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
    }

    # Add docstring to the dynamically generated class
    class_attrs["__doc__"] = (
        f"Renames context key '{original_key}' to '{destination_key}'."
    )

    # Create and return the dynamically named class that inherits from ContextProcessor.
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)


def _context_deleter_factory(key: str) -> type[ContextProcessor]:
    """
    Factory function that creates a ContextProcessor subclass to delete a context key.

    Args:
        key (str): The key to delete.

    Returns:
        Type[ContextProcessor]: A dynamically generated class that removes a key, with a name
                                 of the form "Delete_<key>_Operation".
    """

    def _process_logic(self, **kwargs) -> None:
        """
        Remove a key/value pair from the context using the context observer.

        The key to delete must be provided as a parameter (resolved by the node).
        """
        # Get the key value from parameters (resolved by node) to verify it exists
        value = kwargs.get(key)
        if value is not None:
            # We have the key value, so we can delete the key
            self._notify_context_deletion(key)
            self.logger.debug(f"Deleted context key '{key}'")
        else:
            self.logger.warning(f"Unable to delete non-existing '{key}' from context.")

    # Create a closure that captures the key parameter
    def create_process_logic_with_signature():
        # Create a function with the proper signature using a different approach
        import inspect

        def _process_logic_with_signature(self, **kwargs):
            # Extract the key from kwargs using its name
            key_value = kwargs.get(key)
            if key_value is not None:
                self._notify_context_deletion(key)
                self.logger.debug(f"Deleted context key '{key}'")
            else:
                self.logger.warning(
                    f"Unable to delete non-existing '{key}' from context."
                )

        # Create a new signature with the key as a parameter
        old_sig = inspect.signature(_process_logic_with_signature)
        new_params = [
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(key, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ]
        # Add remaining parameters
        for param in old_sig.parameters.values():
            if param.name not in ["self"]:
                new_params.append(param)

        new_sig = inspect.Signature(new_params)
        _process_logic_with_signature.__signature__ = new_sig
        _process_logic_with_signature.__name__ = "_process_logic_with_signature"
        return _process_logic_with_signature
        return _process_logic_with_signature

    _process_logic = create_process_logic_with_signature()

    def get_required_keys(cls) -> List[str]:
        """
        Return a list with the key to delete, indicating it is required.
        """
        return [key]

    def get_created_keys(cls) -> List[str]:
        """
        This operation does not create any keys.
        """
        return []

    def get_suppressed_keys(cls) -> List[str]:
        """
        Return a list containing the key that is deleted.
        """
        return [key]

    def context_keys(cls) -> List[str]:
        """
        This operation does not modify any persistent keys.
        """
        return []

    # Define the class attributes and methods in a dictionary
    class_attrs = {
        "_process_logic": _process_logic,
        "get_required_keys": classmethod(get_required_keys),
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
        "context_keys": classmethod(context_keys),
    }

    # Create a dynamic class name
    dynamic_class_name = f"Delete_{key}"

    # Add docstring to the dynamically generated class
    class_attrs["__doc__"] = f"Deletes context key '{key}'."

    # Create and return the dynamically named class that inherits from ContextProcessor.
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)
