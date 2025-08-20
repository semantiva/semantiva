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
from semantiva.registry import SemantivaExtension
from semantiva.registry.class_registry import ClassRegistry

class YourExtension(SemantivaExtension):
    def register(self) -> None:
        ClassRegistry.register_modules([
            "your_package.operations",
            "your_package.probes",
            "your_package.data_io"
        ])
```

Pattern 2 - Module-level Register Function:
```python
from semantiva.registry.class_registry import ClassRegistry

def register() -> None:
    ClassRegistry.register_modules([
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
from typing import List, Type
import importlib
import importlib.metadata
from types import ModuleType
from semantiva.logger import Logger

logger = Logger()


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


def load_extensions(specs_to_load: str | List[str]) -> None:
    """Load and register Semantiva extensions by module name.

    This is the primary entry point for loading extensions in both
    development and production environments. It provides a safe, predictable
    mechanism that respects the user's Python environment setup.

    Resolution Process:
    1. **Entry Point Resolution**: First attempts to resolve each name as an
       entry point registered under the group 'semantiva.extensions'.
    2. **Module Import**: If no entry point is found, imports the module by name
       using the standard Python import mechanism.
    3. **Registration**: After successful import, searches the module for
       extension hooks and invokes them to register components.

    Args:
        specs_to_load: Either a single module name (str) or a list of module
                      names (List[str]) to load and register.

    Environment Requirements:
        This function does NOT manipulate sys.path. Modules must be importable
        via the current Python environment through one of:
        - Installed packages (`pip install package_name`)
        - Editable installs (`pip install -e .`)
        - PYTHONPATH environment variable
        - Virtual environment packages

    Raises:
        No exceptions are raised. All errors are logged as warnings to ensure
        robust operation in production environments.

    Examples:
        ```python
        # Load single extension
        load_extensions("semantiva_imaging")

        # Load multiple extensions
        load_extensions(["semantiva_imaging", "semantiva_audio"])

        # Load via YAML (see load_pipeline_from_yaml)
        # extensions: ["semantiva_imaging"]
        ```

    Note:
        For extension developers: Ensure your package exposes either a
        SemantivaExtension subclass or a top-level 'register' function.
        See module docstring for implementation patterns.
    """

    if isinstance(specs_to_load, str):
        specs = [specs_to_load]
    else:
        specs = specs_to_load

    # Collect entry points once for efficiency
    try:
        eps = {
            ep.name: ep
            for ep in importlib.metadata.entry_points(group="semantiva.extensions")
        }
    except TypeError:
        # Python < 3.10 compatibility: entry_points() returns a dict-like object
        eps = {}
        for entry_point in importlib.metadata.entry_points().get(
            "semantiva.extensions", []
        ):
            eps[entry_point.name] = entry_point

    for name in specs:
        # Strategy 1: Try entry point resolution
        ep = eps.get(name)
        if ep is not None:
            try:
                spec_cls: Type[SemantivaExtension] = ep.load()
                if not issubclass(spec_cls, SemantivaExtension):
                    logger.warning(
                        "Warning: Entry point '%s' does not reference a SemantivaExtension subclass. Skipping.",
                        name,
                    )
                    continue
                logger.debug("Loading extension via entry point: %s", name)
                spec_cls().register()
                logger.debug("Successfully registered extension: %s", name)
                continue
            except Exception as e:
                logger.warning("Warning: Failed to load entry point '%s': %s", name, e)

        # Strategy 2: Import by module name
        try:
            mod = importlib.import_module(name)
        except Exception as e:
            logger.warning("Warning: Failed to import module '%s': %s", name, e)
            mod = None

        if isinstance(mod, ModuleType):
            if not _register_from_module(mod):
                logger.warning(
                    "Warning: No Semantiva extension hooks found in module '%s'.", name
                )
            else:
                logger.debug(
                    "Successfully registered Semantiva extension from module: %s", name
                )
        else:
            logger.warning(
                "Warning: No Semantiva extension named '%s' was found.", name
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
    1. Register all their modules with the ClassRegistry
    2. Register any custom resolvers or parameter handlers
    3. Perform any other initialization required for the extension

    Example Implementation:
    ----------------------
    ```python
    from semantiva.registry import SemantivaExtension
    from semantiva.registry.class_registry import ClassRegistry

    class SemantivaImaging(SemantivaExtension):
        def register(self) -> None:
            # Register modules containing processors and data types
            ClassRegistry.register_modules([
                "semantiva_imaging.operations",
                "semantiva_imaging.probes",
                "semantiva_imaging.data_io",
                "semantiva_imaging.data_types"
            ])

            # Optional: Register custom resolvers
            # ClassRegistry.register_resolver(my_custom_resolver)
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
        1. Call `ClassRegistry.register_modules()` with all relevant module names
        2. Register any custom class name resolvers via `ClassRegistry.register_resolver()`
        3. Register any parameter resolvers via `ClassRegistry.register_param_resolver()`
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
