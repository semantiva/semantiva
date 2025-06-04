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

from importlib import import_module
from typing import List, Set
from pathlib import Path
import importlib.util
import re
from semantiva.logger import Logger
from semantiva.context_processors.context_processors import (
    ContextProcessor,
    ContextType,
)


def context_renamer_factory(original_key: str, destination_key: str):
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


def context_deleter_factory(key: str):
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


class ComponentLoader:
    """ComponentLoader is a class that loads components
    from a given set of paths"""

    _registered_paths: Set[Path] = set()
    _registered_modules: Set[str] = set()

    @classmethod
    def initialize_default_modules(cls) -> None:
        """Initialize default modules at the class level"""
        cls._registered_modules.add("semantiva.context_processors.context_processors")

    @classmethod
    def register_paths(cls, paths: str | List[str]):
        """Register a path or a list of paths"""
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            cls._registered_paths.add(Path(path))

    @classmethod
    def register_modules(cls, modules: str | List[str]):
        """Register a module or a list of modules"""
        if isinstance(modules, str):
            modules = [modules]

        for module in modules:
            cls._registered_modules.add(module)

    @classmethod
    def get_registered_paths(cls) -> Set[Path]:
        """Get list of registered paths"""
        return cls._registered_paths

    @classmethod
    def get_registered_modules(cls) -> Set[str]:
        """Get list of registered modules"""
        return cls._registered_modules

    @classmethod
    def get_class(cls, class_name: str):
        """Lookup in registered paths and modules for the class and
        return its type. It starts with modules and then looks in paths."""
        logger = Logger()
        logger.debug(f"Resolving class name {class_name}")

        if class_name.startswith("rename:"):
            match = re.match(r"rename:(.*?):(.*?)$", class_name)
            if match:
                old_key, new_key = match.groups()
                return context_renamer_factory(old_key, new_key)

        elif class_name.startswith("delete:"):
            match = re.match(r"delete:(.*?)$", class_name)
            if match:
                key = match.group(1)
                return context_deleter_factory(key)

        for module_name in cls._registered_modules:
            class_type = cls._get_class_from_module(module_name, class_name)
            if class_type is not None:
                return class_type

        for path in cls._registered_paths:
            class_type = cls._get_class_from_file(path, class_name)
            if class_type is not None:
                return class_type

        raise ValueError(
            f"Class '{class_name}' not found in any of the registered modules and paths."
        )

    @classmethod
    def _get_class_from_module(cls, module_name: str, class_name: str):
        """Lookup in registered modules for the class and
        return its type. If module is not found, return None."""

        try:
            module = import_module(module_name)
            class_type = getattr(module, class_name, None)
            return class_type
        except ModuleNotFoundError:
            return None

    @classmethod
    def _get_class_from_file(cls, file_path: Path, class_name: str):
        """Lookup in registered paths for the class and return its type."""

        if not file_path.is_file():  # If path does not exist, skip it
            return None

        module_name = file_path.stem
        module_spec = importlib.util.spec_from_file_location(module_name, file_path)

        if module_spec is None or not module_spec.loader:
            return None

        module = importlib.util.module_from_spec(module_spec)
        try:
            module_spec.loader.exec_module(module)
        except Exception as e:
            Logger().error(f"Error loading module {module_name}: {e}")
            return None

        # Check and return the class type
        return getattr(module, class_name, None)
