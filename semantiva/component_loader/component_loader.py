import importlib.util
from typing import List, Set
from pathlib import Path


class ComponentLoader:
    """ComponentLoader is a class that loads components
    from a given set of paths"""

    _registered_paths: Set[Path]

    def __init__(self):
        self._registered_paths = set()
        self._register_default_paths()

    def _register_default_paths(self) -> None:
        """Register internal framework paths as
        default"""

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
            self._registered_paths.add(path)

    def register_paths(self, paths: str | List[str]):
        """Register a path or a list of paths"""
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            self._registered_paths.add(Path(path))

    def get_registered_paths(self) -> Set[Path]:
        """Get list of registered paths"""
        return self._registered_paths

    def get_class(self, class_name: str):
        """Lookup in registered paths for the class and
        return its type."""

        for path in self._registered_paths:
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
            cls = getattr(module, class_name, None)
            if cls is not None:
                return cls
        raise ValueError(
            f"Class '{class_name}' not found in any of the registered paths."
        )
