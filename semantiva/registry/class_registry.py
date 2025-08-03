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
from semantiva.data_processors.data_processors import _BaseDataProcessor
from semantiva.context_processors.context_processors import (
    ContextProcessor,
)
from semantiva.context_processors.factory import (
    _context_deleter_factory,
    _context_renamer_factory,
)


class ClassRegistry:
    """ClassRegistry is a class that register classes
    from a given set of paths"""

    _registered_paths: Set[Path] = set()
    _registered_modules: Set[str] = set()

    @classmethod
    def initialize_default_modules(cls) -> None:
        """Initialize default modules at the class level"""
        cls._registered_modules.add("semantiva.context_processors.context_processors")
        cls._registered_modules.add("semantiva.examples.test_utils")

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
        cls, class_name: str
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

        if class_name.startswith("rename:"):
            match = re.match(r"rename:(.*?):(.*?)$", class_name)
            if match:
                old_key, new_key = match.groups()
                return _context_renamer_factory(old_key, new_key)

        elif class_name.startswith("delete:"):
            match = re.match(r"delete:(.*?)$", class_name)
            if match:
                key = match.group(1)
                return _context_deleter_factory(key)

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
