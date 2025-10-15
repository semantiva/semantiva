Registry System
===============

Semantiva's registry system manages component discovery, registration, and resolution
across the framework. This system consists of two main parts: a dual-registry 
architecture for component separation and a bootstrap profile system for reproducible
component loading.

Architecture Overview
---------------------

Semantiva uses a dual-registry system to manage different types of components while
avoiding circular import dependencies. This architecture separates concerns between
general component resolution and execution-specific component management.

Registry Components
~~~~~~~~~~~~~~~~~~~

``ProcessorRegistry``
   Primary registry for data processors, context processors, workflow components,
   data collections, and fitting models. Handles dynamic class discovery from
   modules imported at runtime.

``NameResolverRegistry``
   Stores prefix-based resolvers (``rename:``, ``delete:``, ``template:``,
   ``slice:``) that expand declarative YAML strings into processor classes.

``ParameterResolverRegistry``
   Maintains resolvers that transform configuration values recursively before 
   processor instantiation. Resolvers are applied to dict values, list/tuple items,
   and nested structures. For example, the ``model:`` specification used by 
   fitting pipelines.

:py:class:`~semantiva.execution.component_registry.ExecutionComponentRegistry`
   Specialized registry for execution layer components: orchestrators, executors,
   and transports. Designed to avoid circular import dependencies with graph
   building and general class resolution.

Dependency Separation
~~~~~~~~~~~~~~~~~~~~~

The dual-registry architecture solves a fundamental circular import problem:

* **Graph builder** needs ``ProcessorRegistry`` to resolve processor classes from YAML
* **Orchestrators** need graph builder functions for canonical specs and pipeline IDs
* **ProcessorRegistry** previously needed to import orchestrators for default registration

By introducing ``ExecutionComponentRegistry``, we break this cycle:

.. code-block:: text

   Before (Circular):
   ProcessorRegistry → LocalSemantivaOrchestrator → graph_builder → ProcessorRegistry

   After (Clean):
   ProcessorRegistry → graph_builder
   ExecutionComponentRegistry → LocalSemantivaOrchestrator
   orchestrator/factory → ExecutionComponentRegistry

Parameter Resolver System
-------------------------

Parameter resolvers provide a mechanism to transform configuration values before
processor instantiation. This system enables dynamic configuration resolution,
environment variable substitution, and complex parameter transformations.

Resolution Behavior
~~~~~~~~~~~~~~~~~~~

Parameters are **recursively transformed** before processor instantiation. 
Resolution applies to:

* Dictionary values
* List and tuple items  
* Nested structures (dictionaries within lists, lists within dictionaries, etc.)

Resolvers are run in registration order and should be pure and idempotent.

Adding Custom Parameter Resolvers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a custom parameter resolver:

.. code-block:: python

   from semantiva.registry.parameter_resolver_registry import ParameterResolverRegistry

   def my_param_resolver(value):
       # Return (resolved_value, handled: bool)
       if isinstance(value, str) and value.startswith("myenv:"):
           env_var = value.split(":",1)[1]
           return os.environ.get(env_var, ""), True
       return value, False

   ParameterResolverRegistry.register_resolver("myenv", my_param_resolver)

Built-in Resolvers
~~~~~~~~~~~~~~~~~~

The framework provides several built-in parameter resolvers:

``model:``
   Resolves model specifications into ``ModelDescriptor`` objects for fitting workflows.
   
   Example: ``model:LinearRegression:param1=value1,param2=value2``

Resolver Function Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameter resolver functions must follow this interface:

.. code-block:: python

   def parameter_resolver(value: Any) -> tuple[Any, bool]:
       """Transform a parameter value.
       
       Args:
           value: The input parameter value to potentially transform
           
       Returns:
           tuple: (resolved_value, was_handled)
               - resolved_value: The transformed value (or original if unchanged)
               - was_handled: True if this resolver processed the value, False otherwise
       """

If ``was_handled`` is ``True``, the resolved value is used. If ``False``, the 
original value is passed to the next resolver in the chain.

Recursive Resolution Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Input parameters with nested structure
   payload = {
       "database_url": "myenv:DATABASE_URL",
       "processing_config": {
           "batch_size": 100,
           "model_spec": "model:LinearRegression:learning_rate=0.01"
       },
       "file_paths": ["myenv:INPUT_DIR/file1.txt", "myenv:INPUT_DIR/file2.txt"]
   }
   
   # After recursive parameter resolution
   resolved = {
       "database_url": "postgresql://localhost:5432/mydb",
       "processing_config": {
           "batch_size": 100,
           "model_spec": ModelDescriptor("sklearn.LinearRegression", {"learning_rate": 0.01})
       },
       "file_paths": ["/data/input/file1.txt", "/data/input/file2.txt"]
   }

Bootstrap Profiles
------------------

The **Registry v1** design introduces ``RegistryProfile`` to make registry state
explicit, portable, and reproducible. This system tracks modules and extension
entry points that declare Semantiva components.

Key Concepts
~~~~~~~~~~~~

``RegistryProfile``
    Frozen dataclass capturing four attributes:

    ``load_defaults``
        Whether to ensure the core Semantiva modules and built-in resolvers are
        loaded. Defaults to ``True``.

    ``modules``
        Python modules to import. Importing runs the Semantiva metaclass hooks,
        registering every component exposed by those modules.

    ``extensions``
        Entry-point or module specifications that should be loaded via
        ``semantiva.registry.plugin_registry.load_extensions``.

``apply_profile(profile)``
    Applies ``load_defaults`` (idempotent) and then registers ``modules`` and
    ``extensions`` in that order.

``current_profile()``
    Captures the current process registry and returns a ``RegistryProfile``
    instance. The snapshot always enables ``load_defaults`` and returns the
    module history that has been applied.

``fingerprint()``
    Produces a SHA-256 hash of a normalised representation of the profile. The
    fingerprint is pinned into every SER under ``assertions.environment.registry.fingerprint``.

Initialization Flow
~~~~~~~~~~~~~~~~~~~

Component registration follows a carefully orchestrated initialization sequence:

1. **ProcessorRegistry.register_modules(DEFAULT_MODULES)**

   * Registers core data processors, context processors, and fitting models
   * Ensures built-in resolvers (rename, delete, template, slice, model) are available
   * Calls ``ExecutionComponentRegistry.initialize_defaults()``

2. **ExecutionComponentRegistry.initialize_defaults()**

   * Imports execution components using lazy imports (no circular dependencies)
   * Registers default orchestrators, executors, and transports
   * Safe to call multiple times (idempotent)

Component Resolution
~~~~~~~~~~~~~~~~~~~~

Different component types use their respective registries:

**Data Processors (via resolve_symbol)**:

.. code-block:: python

   from semantiva.registry import ProcessorRegistry, resolve_symbol

   # Ensure modules are registered (idempotent)
   ProcessorRegistry.register_modules(["semantiva.examples.test_utils"])
   processor_cls = resolve_symbol("FloatValueDataSource")

**Execution Components (via ExecutionComponentRegistry)**:

.. code-block:: python

   from semantiva.execution.component_registry import ExecutionComponentRegistry
   
   # Resolves orchestrators for factory
   orch_cls = ExecutionComponentRegistry.get_orchestrator("LocalSemantivaOrchestrator")

Factory Integration
~~~~~~~~~~~~~~~~~~~

The :py:func:`~semantiva.execution.orchestrator.factory.build_orchestrator` function
uses ``ExecutionComponentRegistry`` for component resolution:

.. code-block:: python

   from semantiva.execution.orchestrator.factory import build_orchestrator
   from semantiva.configurations.schema import ExecutionConfig
   
   config = ExecutionConfig(
       orchestrator="LocalSemantivaOrchestrator",
       executor="SequentialSemantivaExecutor",
       transport="InMemorySemantivaTransport"
   )
   
   orchestrator = build_orchestrator(config)

Distributed Execution
---------------------

``QueueSemantivaOrchestrator.enqueue`` now accepts an optional
``registry_profile`` parameter. If omitted, the orchestrator captures the
process state via ``current_profile()``. The profile is attached to job metadata
so that workers can replay the same registry configuration before constructing
pipelines. YAML pipelines keep their ``extensions:`` support—``apply_profile``
is executed before YAML parsing, and ``load_pipeline_from_yaml`` still loads any
inline extensions declared in the file.

Programmatic Usage
------------------

Registry Profiles
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from semantiva.registry.bootstrap import RegistryProfile, apply_profile, current_profile

   # Capture the current process state (defaults, modules, and paths)
   profile = current_profile()

   # Launch a distributed job with an explicit profile
   orchestrator.enqueue(pipeline_nodes, registry_profile=profile)

   # Rehydrate a profile in a worker or a separate process
   apply_profile(profile)

Component Registration
~~~~~~~~~~~~~~~~~~~~~~

**Custom Data Processors**:

.. code-block:: python

   # Register custom processors via ProcessorRegistry
   from semantiva.registry import ProcessorRegistry

   ProcessorRegistry.register_modules(["my_extension.processors"])

**Custom Execution Components**:

.. code-block:: python

   # Register custom orchestrators
   ExecutionComponentRegistry.register_orchestrator(
       "CustomOrchestrator", MyCustomOrchestrator
   )

Best Practices
--------------

1. **Registry Selection**: Use ``resolve_symbol``/``ProcessorRegistry`` for
   data/context processors and ``ExecutionComponentRegistry`` for execution components.

2. **Initialization Order**: Use ``apply_profile`` or
   ``ProcessorRegistry.register_modules`` to ensure required modules are loaded
   before constructing pipelines.

3. **Lazy Imports**: When adding new execution components, use lazy imports in
   ``initialize_defaults()`` to avoid circular dependencies.

4. **Testing**: Both registries provide ``clear()`` methods for test isolation.

5. **Profile Management**: Use ``current_profile()`` to capture reproducible 
   registry states for distributed execution.

Idempotent Defaults
-------------------

``register_builtin_resolvers()`` installs built-in name and parameter resolvers
exactly once. Re-invoking it is safe and preserves any user-provided
resolvers registered with ``NameResolverRegistry`` or
``ParameterResolverRegistry``.

Migration Notes
---------------

The dual-registry architecture was introduced to resolve circular import issues
while maintaining backward compatibility. Existing code using the new
``ProcessorRegistry`` and ``resolve_symbol`` APIs continues to work unchanged.
Only the internal orchestrator factory implementation was modified to use the
execution registry explicitly.

The separation provides a foundation for future scalability, allowing independent
evolution of data processing and execution layer components without coupling concerns.
