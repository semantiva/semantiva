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
Semantiva Plugin Registry
=========================

This module provides a safe, lean mechanism for dynamically loading and
registering Semantiva extensions. It supports both production deployment
via entry points and development environments via module importing.

Key Design Principles:
---------------------
1. **Security**: No sys.path manipulation; relies on proper environment setup
2. **Simplicity**: Single function interface accepting string module names
3. **Flexibility**: Supports entry points, installed packages, and editable installs
4. **Robustness**: Graceful error handling with informative warnings

Extension Implementation Patterns:
--------------------------------------

Pattern 1 - SemantivaExtension Subclass (Recommended):
```python
from semantiva.registry import SemantivaExtension, ProcessorRegistry

class YourExtension(SemantivaExtension):
    def register(self) -> None:
        ProcessorRegistry.register_modules([
            "your_package.operations",
            "your_package.probes",
            "your_package.data_io"
        ])
```

Pattern 2 - Module-level Register Function:
```python
from semantiva.registry import ProcessorRegistry

def register() -> None:
    ProcessorRegistry.register_modules([
        "your_package.operations",
        "your_package.probes",
        "your_package.data_io"
    ])
```

Environment Setup:
-----------------
Modules must be importable via:
- `pip install -e .` (editable install)
- `pip install package_name` (regular install)
- PYTHONPATH environment variable

Usage:
------
```python
from semantiva.registry import load_extensions

load_extensions("your_package")           # Single
load_extensions(["pkg1", "pkg2"])         # Multiple
```
"""

from abc import ABC, abstractmethod
from typing import Iterable, List, Dict, cast
import importlib
from importlib import metadata
from types import ModuleType
from semantiva.logger import Logger

ENTRYPOINT_GROUP = "semantiva.extensions"
logger = Logger()
_LOADED_EXTENSIONS: set[str] = set()


def _register_from_module(mod: ModuleType) -> bool:
    """Discover and register an extension within an imported module.

    This function implements the extension discovery protocol by searching
    for registration hooks in the provided module using two fallback strategies.

    Discovery Strategies:
    1. **SemantivaExtension Subclass**: Searches for the first class that
       subclasses SemantivaExtension, instantiates it, and calls register().
    2. **Module-level Register Function**: If no extension class is found,
       looks for a top-level callable named 'register' and invokes it.

    Args:
        mod: The imported Python module to search for extension hooks.

    Returns:
        bool: True if an extension was found and registered, False otherwise.

    Note:
        This function catches and ignores exceptions during class inspection to
        handle modules that may contain non-class attributes or broken imports.
    """
    # Strategy 1: Find a subclass of SemantivaExtension
    for name in dir(mod):
        obj = getattr(mod, name)
        try:
            if isinstance(obj, type) and issubclass(obj, SemantivaExtension):
                logger.debug(
                    "Registering extension class from module %s: %s", mod.__name__, name
                )
                obj().register()
                return True
        except Exception:
            # Ignore errors during class inspection (e.g., non-classes, import issues)
            continue

    # Strategy 2: Fallback to a top-level register() function
    register_fn = getattr(mod, "register", None)
    if callable(register_fn):
        logger.debug("Calling top-level register() in module %s", mod.__name__)
        register_fn()
        return True

    return False


def load_extensions(specs_to_load: Iterable[str] | str | None) -> None:
    """Load and register Semantiva extensions deterministically.

    Extensions are loaded in sorted order, and each extension is only
    registered once per interpreter session. Both module paths and entry point
    names are supported.

    Args:
        specs_to_load: Sequence of extension identifiers or a single name.

    Raises:
        RuntimeError: If any requested extension cannot be imported or does not
            expose a registration hook.
    """

    if not specs_to_load:
        return

    if isinstance(specs_to_load, str):
        requested = [specs_to_load]
    else:
        requested = list(specs_to_load)

    seen: set[str] = set()
    ordered: List[str] = []
    for item in requested:
        if item not in seen:
            seen.add(item)
            ordered.append(item)

    ordered.sort()

    resolved: set[str] = set()
    module_notes: Dict[str, str] = {}

    for ref in ordered:
        if ref in _LOADED_EXTENSIONS:
            logger.debug("Extension '%s' already loaded; skipping", ref)
            resolved.add(ref)
            continue
        try:
            module = importlib.import_module(ref)
        except Exception as exc:
            module_notes.setdefault(ref, f"import error: {exc}")
            continue
        try:
            if _register_from_module(module):
                logger.debug("Registered extension via module import: %s", ref)
                _LOADED_EXTENSIONS.add(ref)
                resolved.add(ref)
                continue
        except Exception as exc:  # pragma: no cover - extension bugs
            raise RuntimeError(
                f"Extension '{ref}' raised an error during register(): {exc}"
            ) from exc
        module_notes.setdefault(ref, "no register() hook found")

    remaining = [name for name in ordered if name not in resolved]
    if not remaining:
        return

    try:
        entry_points = list(metadata.entry_points(group=ENTRYPOINT_GROUP))
    except TypeError:  # pragma: no cover - legacy importlib.metadata API
        groups = cast(Dict[str, Iterable[metadata.EntryPoint]], metadata.entry_points())
        entry_points = list(groups.get(ENTRYPOINT_GROUP, []))

    entry_points.sort(key=lambda ep: (ep.name or "", ep.value or ""))

    for ep in entry_points:
        if ep.name not in remaining or ep.name in _LOADED_EXTENSIONS:
            continue
        try:
            target = ep.load()
        except Exception as exc:  # pragma: no cover - entry point import errors
            raise RuntimeError(
                f"Entry point '{ep.name}' could not be loaded: {exc}"
            ) from exc
        try:
            if isinstance(target, type):
                if issubclass(target, SemantivaExtension):
                    target().register()
                else:
                    raise RuntimeError(
                        f"Entry point '{ep.name}' did not return a callable or an object with register()"
                    )
            elif callable(target):
                target()
            elif hasattr(target, "register") and callable(target.register):
                target.register()
            else:
                raise RuntimeError(
                    f"Entry point '{ep.name}' did not return a callable or an object with register()"
                )
        except Exception as exc:  # pragma: no cover - extension bugs
            raise RuntimeError(
                f"Extension '{ep.name}' raised an error during register(): {exc}"
            ) from exc
        logger.debug("Registered extension via entry point: %s", ep.name)
        _LOADED_EXTENSIONS.add(ep.name)
        resolved.add(ep.name)

    missing = [name for name in ordered if name not in resolved]
    if missing:
        details = [
            f"{name} ({module_notes.get(name, 'not found')})" for name in missing
        ]
        raise RuntimeError(
            "Could not load extensions: "
            + ", ".join(details)
            + f". Ensure they expose entry point group '{ENTRYPOINT_GROUP}' or a module-level register()."
        )


class SemantivaExtension(ABC):
    """Abstract base class for Semantiva domain extensions.

    This class defines the contract that all Semantiva extensions must
    implement to provide consistent registration behavior across the ecosystem.

    Extensions are domain-specific extensions that add new data types,
    operations, probes, and I/O capabilities to the core Semantiva framework.
    Examples include image processing, audio processing, or scientific computing
    domains.

    Implementation Requirements:
    ---------------------------
    Subclasses must implement the `register()` method to:
    1. Register all their modules with :class:`~semantiva.registry.ProcessorRegistry`
    2. Register any custom name or parameter resolvers if required
    3. Perform any other initialization required for the extension

    Example Implementation:
    ----------------------
    ```python
    from semantiva.registry import SemantivaExtension, ProcessorRegistry

    class SemantivaImaging(SemantivaExtension):
        def register(self) -> None:
            # Register modules containing processors and data types
            ProcessorRegistry.register_modules([
                "semantiva_imaging.operations",
                "semantiva_imaging.probes",
                "semantiva_imaging.data_io",
                "semantiva_imaging.data_types"
            ])

            # Optional: Register custom resolvers via NameResolverRegistry
    ```

    Usage:
    ------
    Extension classes are typically not instantiated directly by users.
    Instead, they are discovered and instantiated automatically by the
    `load_extensions()` function when loading an extension by name.

    Thread Safety:
    -------------
    Implementations should ensure that the `register()` method is idempotent
    and thread-safe, as it may be called multiple times in concurrent
    environments.
    """

    @abstractmethod
    def register(self) -> None:
        """Register all components of this extension with Semantiva.

        This method is called automatically when the extension is loaded
        via `load_extensions()`. It should register all modules, classes,
        and any custom resolvers required for the extension to function.

        The implementation should:
        1. Call :func:`ProcessorRegistry.register_modules` with all relevant module names
        2. Register any custom class name resolvers via :class:`NameResolverRegistry`
        3. Register any parameter resolvers via :class:`ParameterResolverRegistry`
        4. Perform any other one-time initialization

        Raises:
            Should not raise exceptions under normal circumstances. Any errors
            should be logged and handled gracefully to avoid breaking the
            overall extension loading process.

        Note:
            This method should be idempotent - calling it multiple times should
            have the same effect as calling it once.
        """
        pass
