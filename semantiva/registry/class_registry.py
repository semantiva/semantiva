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
special cases like renaming, deletion, slicing, or parametric sweep operations.

Custom Resolver System
---------------------
The registry supports pluggable resolvers via the `register_resolver` API. A
resolver is a callable that takes a class name string and returns a class type
(or None if it does not handle the name). This allows the registry to support
arbitrary prefixes (e.g., `rename:`, `delete:`, `slicer:`, `sweep:`) without
modifying core logic. New resolvers can be registered at runtime, enabling
extensibility for future processor types or domain-specific behaviors.

How Resolution Works
--------------------
When `ClassRegistry.get_class(class_name)` is called:
1. All registered custom resolvers are consulted in order. If any resolver returns a non-None class, it is used.
2. If no resolver matches, the registry attempts to locate the class in registered modules and file paths.
3. If the class cannot be found, a ValueError is raised.

Default Resolvers
-----------------
By default, the registry registers resolvers for:
* `rename:` — Handles context renaming operations.
* `delete:` — Handles context deletion operations.
* `slicer:` — Handles slicing operations, allowing YAML pipelines to specify slicing processors.

Special Processing
------------------
The `sweep:` prefix for parametric sweeps requires access to configuration parameters
and is handled by `preprocess_node_config()` before standard resolution occurs. This
preprocessing validates sweep parameters and creates the appropriate processor class.

Parametric Sweep Resolver Usage
------------------------------
The `sweep:` resolver creates parametric sweep processors that generate collections of data
by varying independent parameters over specified ranges. Only the structured YAML format is supported:

    processor: "sweep:DataSourceClass:CollectionClass"
    parameters:
      num_steps: <number>
      independent_vars:
        var_name: [min, max]
      parametric_expressions:
        param_name: "expression"
      static_params:
        param_name: value

Example:
    processor: "sweep:FloatMockDataSource:FloatDataCollection"
    parameters:
      num_steps: 5
      independent_vars:
        t: [0, 10]
      parametric_expressions:
        x_0: "50 + 5 * t"
        amplitude: "100"
      static_params:
        image_size: [128, 128]

The sweep processor:
1. Creates sequences for each independent variable using np.linspace
2. Stores parameter sequences in context as `{var}_values`
3. Evaluates expressions for each step using current parameter values
4. Calls the data source with computed parameters to generate data elements
5. Returns a collection containing all generated data elements
"""

from importlib import import_module
from pathlib import Path
import importlib.util
import re
from typing import Any, Callable, Dict, List, Optional, Set, cast

from semantiva.logger import Logger
from semantiva.data_processors.data_processors import _BaseDataProcessor
from semantiva.data_processors.data_slicer_factory import slicer
from semantiva.data_processors.parametric_sweep_factory import ParametricSweepFactory
from semantiva.data_io.data_io import DataSource
from semantiva.data_types.data_types import DataCollectionType
from semantiva.context_processors.context_processors import (
    ContextProcessor,
)
from semantiva.context_processors.factory import (
    _context_deleter_factory,
    _context_renamer_factory,
)
from semantiva.workflows.fitting_model import FittingModel
from .descriptors import ModelDescriptor


class ClassRegistry:
    """
    ClassRegistry is a central registry for resolving class types by name,
    supporting both standard and custom resolution strategies.

    It maintains lists of registered file paths, modules, and pluggable resolver
    """

    _registered_paths: Set[Path] = set()
    _registered_modules: Set[str] = set()
    _custom_resolvers: List[Callable[[str], Optional[type]]] = []
    _param_resolvers: List[Callable[[Any], Optional[Any]]] = []

    @classmethod
    def initialize_default_modules(cls) -> None:
        """Initialize default modules at the class level"""
        cls._registered_modules.add("semantiva.context_processors.context_processors")
        cls._registered_modules.add("semantiva.examples.test_utils")
        cls._registered_modules.add("semantiva.workflows.fitting_model")

        cls._custom_resolvers = []
        cls._param_resolvers = []
        cls.register_resolver(_rename_resolver)
        cls.register_resolver(_delete_resolver)
        cls.register_resolver(_slicer_resolver)
        cls.register_param_resolver(_model_param_resolver)

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
    def register_param_resolver(
        cls, resolver_fn: Callable[[Any], Optional[Any]]
    ) -> None:
        """Register a resolver for parameter values.

        Resolvers are called for every string parameter encountered while
        loading a pipeline configuration. If a resolver returns a non-``None``
        value, that value replaces the original string.

        Args:
            resolver_fn: Callable that takes the parameter specification and
                returns a resolved value or ``None`` if it does not handle the
                input.
        """

        cls._param_resolvers.append(resolver_fn)

    @classmethod
    def resolve_parameters(cls, obj: Any) -> Any:
        """Recursively resolve parameters using registered resolvers."""
        if isinstance(obj, dict):
            return {k: cls.resolve_parameters(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [cls.resolve_parameters(v) for v in obj]
        if isinstance(obj, str):
            for resolver in cls._param_resolvers:
                resolved = resolver(obj)
                if resolved is not None:
                    return resolved
            return obj
        return obj

    @classmethod
    def preprocess_node_config(cls, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess node configuration to handle structured sweep definitions.

        ARCHITECTURAL JUSTIFICATION:
        ===========================
        This preprocessing step exists to bridge a fundamental architectural gap in the
        resolver system when handling structured YAML configurations that require access
        to both processor specifications and parameter sections.

        THE RESOLVER LIMITATION:
        Traditional resolvers follow the pattern: string -> class
        Example: "slicer:Processor:Collection" -> SomeProcessorClass

        They operate in isolation on processor strings and cannot access the broader
        node configuration context (parameters, context_keyword, etc.).

        THE STRUCTURED SWEEP CHALLENGE:
        Structured parametric sweeps require data from multiple YAML sections:

        processor: "sweep:Source:Collection"     # <- Traditional resolver domain
        parameters:                              # <- Outside resolver scope
          num_steps: 5                          # <- Required for ParametricSweepFactory
          independent_vars: { t: [0, 10] }      # <- Required for ParametricSweepFactory

        WHY NOT EXTEND RESOLVERS:
        1. Breaking Change: Would require modifying all existing resolver signatures
        2. Architectural Violation: Resolvers are designed for string-to-class mapping
        3. Complexity: Would need to pass node context to every resolver call
        4. Performance: All resolvers would need to handle additional parameters

        PREPROCESSING DESIGN BENEFITS:
        1. Non-invasive: Existing resolvers remain unchanged
        2. Targeted: Only affects structured sweep configurations
        3. Maintainable: Clear separation of concerns
        4. Extensible: Pattern can be reused for other structured formats
        5. Performance: Only processes relevant configurations

        PROCESSING FLOW:
        1. Check if processor matches structured sweep pattern
        2. Validate presence of required parameters (num_steps, independent_vars)
        3. Transform parameters into ParametricSweepFactory.create() arguments
        4. Create sweep processor class using factory
        5. Return modified node config with resolved processor and empty parameters
        6. Fall back to standard resolution if structured processing fails

        LIMITATIONS AND TRADEOFFS:
        - Adds complexity to node factory processing pipeline
        - Creates special-case handling for one resolver type
        - Couples ClassRegistry more tightly to specific processor types
        - May need extension if other structured formats are added

        ALTERNATIVE ARCHITECTURES CONSIDERED:
        1. Enhanced Resolver Protocol: resolver(processor_str, node_config) -> class
           - Pros: Unified approach, full context access
           - Cons: Breaking change, affects all resolvers, over-engineering

        2. Two-Phase Resolution: first resolve type, then resolve configuration
           - Pros: Clean separation
           - Cons: Complex, requires resolver registry changes

        3. Configuration Processors: separate system for config transformation
           - Pros: Complete separation of concerns
           - Cons: Additional complexity, parallel processing system

        The preprocessing approach was chosen as the minimal viable solution that
        addresses the immediate need while preserving system stability and
        maintaining clear upgrade paths for future enhancements.

        Args:
            node_config: Node configuration with processor and parameters

        Returns:
            Modified configuration with resolved processor for sweep: prefix,
            or unchanged configuration otherwise

        Raises:
            ValueError: If sweep configuration is invalid
        """
        processor_spec = node_config.get("processor")
        parameters = node_config.get("parameters", {})

        # Handle sweep: prefix with structured parameters
        if (
            isinstance(processor_spec, str)
            and processor_spec.startswith("sweep:")
            and "num_steps" in parameters
            and "independent_vars" in parameters
        ):

            parts = processor_spec.split(":")
            if len(parts) == 3:
                try:
                    _, source_name, collection_name = parts

                    # Validate num_steps
                    num_steps = parameters.get("num_steps")
                    if not isinstance(num_steps, int) or num_steps <= 1:
                        raise ValueError("num_steps must be an integer greater than 1")

                    # Validate and process independent_vars
                    independent_vars = parameters.get("independent_vars", {})
                    if not isinstance(independent_vars, dict) or not independent_vars:
                        raise ValueError(
                            "independent_vars must be a non-empty dictionary"
                        )

                    processed_vars = {}
                    for var, range_spec in independent_vars.items():
                        if isinstance(range_spec, list) and len(range_spec) == 2:
                            processed_vars[var] = (
                                float(range_spec[0]),
                                float(range_spec[1]),
                            )
                        else:
                            raise ValueError(
                                f"Variable '{var}' must have range format [min, max]"
                            )

                    # Validate optional parameters
                    parametric_expressions = parameters.get(
                        "parametric_expressions", {}
                    )
                    if not isinstance(parametric_expressions, dict):
                        raise ValueError("parametric_expressions must be a dictionary")

                    static_params = parameters.get("static_params", {})
                    if not isinstance(static_params, dict):
                        raise ValueError("static_params must be a dictionary")

                    # Resolve classes and create sweep processor
                    source_cls = cls.get_class(source_name, use_resolvers=False)
                    collection_cls = cls.get_class(collection_name, use_resolvers=False)

                    if not issubclass(source_cls, DataSource):
                        raise ValueError(f"{source_name} is not a DataSource subclass")
                    if not issubclass(collection_cls, DataCollectionType):
                        raise ValueError(
                            f"{collection_name} is not a DataCollectionType subclass"
                        )

                    sweep_class = ParametricSweepFactory.create(
                        element_source=source_cls,
                        collection_output=collection_cls,
                        independent_vars=processed_vars,
                        parametric_expressions=parametric_expressions,
                        num_steps=num_steps,
                        static_params=static_params if static_params else None,
                    )

                    return {**node_config, "processor": sweep_class, "parameters": {}}

                except ValueError:
                    # Re-raise validation errors (these should be caught by tests)
                    raise
                except Exception:
                    # Fall back to standard resolution on other errors
                    pass

        return node_config

    @classmethod
    def register_config_processor(
        cls, processor_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Register a configuration processor for future extensibility.

        FUTURE IMPROVEMENT PATHWAY:
        ==========================
        The current preprocessing approach could be generalized into a more flexible
        configuration processor system. This would allow:

        1. Multiple configuration transformers
        2. Ordered processing pipeline
        3. Cleaner separation of concerns
        4. Easier testing and maintenance

        Example usage:
            @ClassRegistry.register_config_processor
            def structured_sweep_processor(config):
                # Handle sweep: prefix with parameters
                return transformed_config

            @ClassRegistry.register_config_processor
            def other_structured_processor(config):
                # Handle other complex configurations
                return transformed_config

        This would replace the current hardcoded preprocessing with a pluggable system
        similar to how resolvers work for simple string-to-class mappings.

        Args:
            processor_fn: Function that takes a node configuration dict and returns
                         a potentially modified configuration dict
        """
        # Implementation would add to a _config_processors list
        # and iterate through them in preprocess_node_config
        pass  # Placeholder for future implementation

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
    ) -> Optional[type[ContextProcessor | _BaseDataProcessor]]:
        """Lookup in registered modules for the class and
        return its type. If module is not found, return None.

        Args:
            module_name (str): The name of the module for searching.
            class_name (str): The class name of the context processor or base data processor.

        Returns:
            Optional[type[ContextProcessor | _BaseDataProcessor]]: The type of the ContextProcessor or _BaseDataProcessor. If not found, returns None.

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
    ) -> Optional[type[ContextProcessor | _BaseDataProcessor]]:
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
            return slicer(processor_t, collection_t)
    return None


def _parse_scalar(value: str) -> Any:
    """Best-effort conversion of a string to int, float, bool, or str."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _model_param_resolver(spec: Any) -> Optional[ModelDescriptor]:
    """Return a :class:`ModelDescriptor` from ``model:``-prefixed specs.

    The expected format is ``model:ClassName:k1=v1,k2=v2``.  The class name is
    resolved using :meth:`ClassRegistry.get_class` and keyword arguments are
    parsed as simple scalars, but **not** instantiated.  This keeps the
    canonical specification free of live objects while retaining enough
    information to construct the model later.
    """

    if isinstance(spec, str) and spec.startswith("model:"):
        _, remainder = spec.split("model:", 1)
        class_part, _, arg_part = remainder.partition(":")
        model_cls = ClassRegistry.get_class(class_part)
        if not issubclass(model_cls, FittingModel):
            raise ValueError(f"{class_part} is not a FittingModel subclass")
        kwargs = {}
        if arg_part:
            for item in arg_part.split(","):
                if not item:
                    continue
                key, _, val = item.partition("=")
                kwargs[key] = _parse_scalar(val)
        class_path = f"{model_cls.__module__}.{model_cls.__qualname__}"
        return ModelDescriptor(class_path, kwargs)
    return None
