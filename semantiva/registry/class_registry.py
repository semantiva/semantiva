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

"""
Class Registry
==============

Overview
--------
The `ClassRegistry` provides a unified mechanism for dynamically registering and
resolving classes by name, supporting both standard class lookups and custom
prefix-based resolution. This is essential for pipeline definitions that use
text-based configuration (e.g., YAML) to specify processor types, including
special cases like renaming, deletion, or slicing operations.

Custom Resolver System
---------------------
The registry supports pluggable resolvers via the `register_resolver` API. A 
resolver is a callable that takes a class name string and returns a class type
(or None if it does not handle the name). This allows the registry to support 
arbitrary prefixes (e.g., `rename:`, `delete:`, `slicer:`) without modifying 
core logic. New resolvers can be registered at runtime, enabling extensibility
for future processor types or domain-specific behaviors.

How Resolution Works
--------------------
When `ClassRegistry.get_class(class_name)` is called:
1. All registered custom resolvers are consulted in order. If any resolver returns a non-None class, it is used.
2. If no resolver matches, the registry attempts to locate the class in registered modules and file paths.
3. If the class cannot be found, a ValueError is raised.

Default Resolvers
-----------------
By default, the registry registers three resolvers:
* `rename:` — Handles context renaming operations.
* `delete:` — Handles context deletion operations.
* `slicer:` — Handles slicing operations, allowing YAML pipelines to specify slicing processors.
"""

from importlib import import_module
from typing import Callable, List, Optional, Set, cast
from pathlib import Path
import importlib.util
import re
from semantiva.logger import Logger
from semantiva.data_processors.data_processors import _BaseDataProcessor
from semantiva.data_processors.data_slicer_factory import Slicer
from semantiva.data_types.data_types import DataCollectionType
from semantiva.context_processors.context_processors import (
    ContextProcessor,
)
from semantiva.context_processors.factory import (
    _context_deleter_factory,
    _context_renamer_factory,
)


class ClassRegistry:
    """
    ClassRegistry is a central registry for resolving class types by name,
    supporting both standard and custom resolution strategies.

    It maintains lists of registered file paths, modules, and pluggable resolver
    """

    _registered_paths: Set[Path] = set()
    _registered_modules: Set[str] = set()
    _custom_resolvers: List[Callable[[str], Optional[type]]] = []

    @classmethod
    def initialize_default_modules(cls) -> None:
        """Initialize default modules at the class level"""
        cls._registered_modules.add("semantiva.context_processors.context_processors")
        cls._registered_modules.add("semantiva.examples.test_utils")

        cls._custom_resolvers = []
        cls.register_resolver(_rename_resolver)
        cls.register_resolver(_delete_resolver)
        cls.register_resolver(_slicer_resolver)

    @classmethod
    def register_resolver(cls, resolver_fn: Callable[[str], Optional[type]]) -> None:
        """
        Register a custom resolver function for class name resolution.

        A resolver is a callable that takes a class name string and returns a
        class type if it can handle the name, or None otherwise.

        Args:
            resolver_fn (Callable[[str], Optional[type]]): A function that takes a string and returns a class type or None.
        """
        cls._custom_resolvers.append(resolver_fn)

    @classmethod
    def register_paths(cls, paths: str | List[str]) -> None:
        """Register a path or a list of paths"""
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            cls._registered_paths.add(Path(path))

    @classmethod
    def register_modules(cls, modules: str | List[str]) -> None:
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
    def get_class(
        cls, class_name: str, *, use_resolvers: bool = True
    ) -> type[ContextProcessor] | type[_BaseDataProcessor]:
        """Lookup in registered paths and modules for the class and
        return its type. It starts with modules and then looks in paths.

        Args:
            class_name (str): The class name of the context processor or base data processor.

        Returns:
            ContextProcessor | _BaseDataProcessor: The type of the ContextProcessor or _BaseDataProcessor.

        """
        logger = Logger()
        logger.debug(f"Resolving class name {class_name}")

        if use_resolvers:
            for resolver in cls._custom_resolvers:
                resolved = resolver(class_name)
                if resolved is not None:
                    return resolved

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
    def _get_class_from_module(
        cls, module_name: str, class_name: str
    ) -> type[ContextProcessor] | type[_BaseDataProcessor] | None:
        """Lookup in registered modules for the class and
        return its type. If module is not found, return None.

        Args:
            module_name (str): The name of the module for searching.
            class_name (str): The class name of the context processor or base data processor.

        Returns:
            ContextProcessor | _BaseDataProcessor | None: The type of the ContextProcessor or _BaseDataProcessor. If not found, returns None.

        """

        try:
            module = import_module(module_name)
            class_type = getattr(module, class_name, None)
            return class_type
        except ModuleNotFoundError:
            return None

    @classmethod
    def _get_class_from_file(
        cls, file_path: Path, class_name: str
    ) -> type[ContextProcessor] | type[_BaseDataProcessor] | None:
        """Lookup in registered paths for the class and return its type.

        Args:
            file_path (str): The path of the file for searching.
            class_name (str): The class name of the context processor or base data processor.

        Returns:
            ContextProcessor | _BaseDataProcessor: The type of the ContextProcessor or _BaseDataProcessor. If not found, returns None.

        """

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


def _rename_resolver(name: str) -> Optional[type]:
    """Resolver for the ``rename:`` prefix."""
    if name.startswith("rename:"):
        match = re.match(r"rename:(.*?):(.*?)$", name)
        if match:
            old_key, new_key = match.groups()
            return _context_renamer_factory(old_key, new_key)
    return None


def _delete_resolver(name: str) -> Optional[type]:
    """Resolver for the ``delete:`` prefix."""
    if name.startswith("delete:"):
        match = re.match(r"delete:(.*?)$", name)
        if match:
            key = match.group(1)
            return _context_deleter_factory(key)
    return None


def _slicer_resolver(name: str) -> Optional[type]:
    """Resolver for the ``slicer:`` prefix."""
    if name.startswith("slicer:"):
        match = re.match(r"slicer:(.*?):(.*?)$", name)
        if match:
            processor_name, collection_name = match.groups()
            processor_cls = ClassRegistry.get_class(processor_name, use_resolvers=False)
            collection_cls = ClassRegistry.get_class(
                collection_name, use_resolvers=False
            )
            if not issubclass(processor_cls, _BaseDataProcessor):
                raise ValueError(f"{processor_name} is not a DataProcessor subclass")
            if not issubclass(collection_cls, DataCollectionType):
                raise ValueError(
                    f"{collection_name} is not a DataCollectionType subclass"
                )
            processor_t = cast(type[_BaseDataProcessor], processor_cls)
            collection_t = cast(type[DataCollectionType], collection_cls)
            return Slicer(processor_t, collection_t)
    return None
