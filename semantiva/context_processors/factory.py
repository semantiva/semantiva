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
    ContextType,
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

    def _process_logic(self, context: ContextType) -> ContextType:
        """
        Rename a context key.

        Args:
            context (ContextType): The context to modify.

        Returns:
            ContextType: The updated context with the key renamed.
        """
        if original_key in context.keys():
            value = context.get_value(original_key)
            context.set_value(destination_key, value)
            context.delete_value(original_key)
            self.logger.debug(
                f"Renamed context key '{original_key}' -> '{destination_key}'"
            )
        else:
            self.logger.warning(f"Key '{original_key}' not found in context.")
        return context

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

    # Create a dynamic class name that clearly shows the renaming transformation
    dynamic_class_name = f"Rename_{original_key}_to_{destination_key}"

    # Define the class attributes and methods in a dictionary
    class_attrs = {
        # "__name__": dynamic_class_name,
        "_process_logic": _process_logic,
        "get_required_keys": classmethod(get_required_keys),
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": classmethod(get_suppressed_keys),
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

    def _process_logic(self, context: ContextType) -> ContextType:
        """
        Remove a key/value pair from the context.

        Args:
            context (ContextType): The input context.

        Returns:
            ContextType: The updated context with the key removed.
        """
        if key in context.keys():
            context.delete_value(key)
            self.logger.debug(f"Deleted context key '{key}'")
        else:
            self.logger.warning(f"Unable to delete non-existing '{key}' from context.")
        return context

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

    # Define the class attributes and methods in a dictionary
    class_attrs = {
        "_process_logic": _process_logic,
        "get_required_keys": get_required_keys,
        "get_created_keys": classmethod(get_created_keys),
        "get_suppressed_keys": get_suppressed_keys,
    }

    # Create a dynamic class name
    dynamic_class_name = f"Delete_{key}"

    # Add docstring to the dynamically generated class
    class_attrs["__doc__"] = f"Deletes context key '{key}'."

    # Create and return the dynamically named class that inherits from ContextProcessor.
    return type(dynamic_class_name, (ContextProcessor,), class_attrs)
