import importlib.util
from typing import List, Set
from pathlib import Path


class ComponentLoader:
    """ComponentLoader is a class that loads components
    from a given set of paths"""

    _registered_paths: Set[Path] = set()

    @classmethod
    def initialize_default_paths(cls) -> None:
        """Initialize default paths at the class level"""
        # Get the current file's directory and resolve project root
        current_dir = Path(__file__).resolve().parent.parent
        base_path = current_dir.parent / "semantiva"

        default_paths_list = [
            "specializations/image/image_algorithms.py",
            "specializations/image/image_probes.py",
            "context_operations/context_operations.py",
        ]

        # Use the base_path in the loop
        for relative_path in default_paths_list:
            path = base_path / relative_path
            cls._registered_paths.add(path)

    @classmethod
    def register_paths(cls, paths: str | List[str]):
        """Register a path or a list of paths"""
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            cls._registered_paths.add(Path(path))

    @classmethod
    def get_registered_paths(cls) -> Set[Path]:
        """Get list of registered paths"""
        return cls._registered_paths

    @classmethod
    def get_class(cls, class_name: str):
        """Lookup in registered paths for the class and
        return its type."""

        for path in cls._registered_paths:
            if not path.is_file():  # If path does not exist, skip it
                continue

            module_name = path.stem
            module_spec = importlib.util.spec_from_file_location(module_name, path)

            if module_spec is None or not module_spec.loader:
                continue

            module = importlib.util.module_from_spec(module_spec)
            try:
                module_spec.loader.exec_module(module)
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
                continue

            # Check and return the class type
            class_type = getattr(module, class_name, None)
            if class_type is not None:
                return class_type
        raise ValueError(
            f"Class '{class_name}' not found in any of the registered paths."
        )


# Initialize default paths when the class is loaded
ComponentLoader.initialize_default_paths()
