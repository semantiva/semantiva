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

``ClassRegistry``
   Primary registry for data processors, context processors, and workflow components.
   Handles dynamic class resolution from YAML configurations, custom resolvers,
   and module/path registration.

:py:class:`~semantiva.execution.component_registry.ExecutionComponentRegistry`
   Specialized registry for execution layer components: orchestrators, executors,
   and transports. Designed to avoid circular import dependencies with graph
   building and general class resolution.

Dependency Separation
~~~~~~~~~~~~~~~~~~~~~

The dual-registry architecture solves a fundamental circular import problem:

* **Graph builder** needs ``ClassRegistry`` to resolve processor classes from YAML
* **Orchestrators** need graph builder functions for canonical specs and pipeline IDs  
* **ClassRegistry** needed to import orchestrators for default registration

By introducing ``ExecutionComponentRegistry``, we break this cycle:

.. code-block:: text

   Before (Circular):
   ClassRegistry → LocalSemantivaOrchestrator → graph_builder → ClassRegistry

   After (Clean):
   ClassRegistry → graph_builder
   ExecutionComponentRegistry → LocalSemantivaOrchestrator
   orchestrator/factory → ExecutionComponentRegistry

Bootstrap Profiles
------------------

The **Registry v1** design introduces ``RegistryProfile`` to make registry state
explicit, portable, and reproducible. This system tracks modules, filesystem paths,
and extension entry points that declare Semantiva components.

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

    ``paths``
        Filesystem paths that should be scanned for component definitions.

    ``extensions``
        Entry-point or module specifications that should be loaded via
        ``semantiva.registry.plugin_registry.load_extensions``.

``apply_profile(profile)``
    Applies ``load_defaults`` (idempotent) and then registers ``paths``,
    ``modules``, and ``extensions`` in that order.

``current_profile()``
    Captures the current process registry and returns a ``RegistryProfile``
    instance. The snapshot always enables ``load_defaults`` and returns the
    currently registered modules and paths.

``fingerprint()``
    Produces a SHA-256 hash of a normalised representation of the profile. The
    fingerprint is pinned into every SER under ``why_ok.env.registry.fingerprint``.

Initialization Flow
~~~~~~~~~~~~~~~~~~~

Component registration follows a carefully orchestrated initialization sequence:

1. **ClassRegistry.initialize_default_modules()**

   * Registers core data processors and context processors
   * Sets up built-in resolvers (rename, delete, slicer, model)
   * Calls ``ExecutionComponentRegistry.initialize_defaults()``

2. **ExecutionComponentRegistry.initialize_defaults()**

   * Imports execution components using lazy imports (no circular dependencies)
   * Registers default orchestrators, executors, and transports
   * Safe to call multiple times (idempotent)

Component Resolution
~~~~~~~~~~~~~~~~~~~~

Different component types use their respective registries:

**Data Processors (via ClassRegistry)**:

.. code-block:: python

   from semantiva.registry.class_registry import ClassRegistry
   
   # Resolves processors from YAML
   processor_cls = ClassRegistry.get_class("FloatValueDataSource")

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

   # Register custom processors via ClassRegistry
   ClassRegistry.register_modules(["my_extension.processors"])

**Custom Execution Components**:

.. code-block:: python

   # Register custom orchestrators
   ExecutionComponentRegistry.register_orchestrator(
       "CustomOrchestrator", MyCustomOrchestrator
   )

Best Practices
--------------

1. **Registry Selection**: Use ``ClassRegistry`` for data/context processors,
   ``ExecutionComponentRegistry`` for execution components.

2. **Initialization Order**: Always call ``ClassRegistry.initialize_default_modules()``
   before using either registry.

3. **Lazy Imports**: When adding new execution components, use lazy imports in
   ``initialize_defaults()`` to avoid circular dependencies.

4. **Testing**: Both registries provide ``clear()`` methods for test isolation.

5. **Profile Management**: Use ``current_profile()`` to capture reproducible 
   registry states for distributed execution.

Idempotent Defaults
-------------------

``ClassRegistry.initialize_default_modules()`` no longer clears custom
resolvers when loading defaults, and built-in resolvers are installed once.
Calling the method repeatedly is safe and preserves any user-provided
resolvers.

Migration Notes
---------------

The dual-registry architecture was introduced to resolve circular import issues
while maintaining backward compatibility. Existing code using ``ClassRegistry`` 
for data processors continues to work unchanged. Only the internal orchestrator 
factory implementation was modified to use the new execution registry.

The separation provides a foundation for future scalability, allowing independent
evolution of data processing and execution layer components without coupling concerns.
