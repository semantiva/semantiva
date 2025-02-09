import importlib.util
from importlib import import_module
from typing import List, Set
from pathlib import Path


class ComponentLoader:
    """ComponentLoader is a class that loads components
    from a given set of paths"""

    _registered_paths: Set[Path] = set()
    _registered_modules: Set[str] = set()

    @classmethod
    def initialize_default_modules(cls) -> None:
        """Initialize default modules at the class level"""
        cls._registered_modules.add("semantiva.specializations.image.image_algorithms")
        cls._registered_modules.add("semantiva.specializations.image.image_probes")
        cls._registered_modules.add("semantiva.context_operations.context_operations")

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
            print(f"Error loading module {module_name}: {e}")
            return None

        # Check and return the class type
        return getattr(module, class_name, None)


# Initialize default modules when the class is loaded
ComponentLoader.initialize_default_modules()
