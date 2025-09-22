Extending Semantiva (Registries & Extensions)
=============================================
(SSoT) This page mirrors `semantiva/registry/*`. Update this doc if registry changes.

Overview
--------
Register domain components (operations, probes, sources/sinks, context processors)
and custom resolvers using the plugin registry.

Implement an Extension
----------------------
Subclass ``SemantivaExtension`` and implement ``register()``. When registering
execution-layer integrations (orchestrators, executors, transports), call the
Execution Component Registry (ECR):

.. code-block:: python

    from semantiva.execution.component_registry import ExecutionComponentRegistry as ECR
    from semantiva.registry import SemantivaExtension, ClassRegistry

    class MyDomainExtension(SemantivaExtension):
        def register(self) -> None:
            ClassRegistry.register_modules([
                "my_pkg.ops",      # DataOperation/DataProbe subclasses
                "my_pkg.io",       # DataSource/DataSink
                "my_pkg.context",  # ContextProcessor
            ])
            # Register execution components
            ECR.register_orchestrator("my-local", MyLocalOrchestrator)

            # Optional: custom class-name resolvers (e.g., "rename:Old:New")
            # ClassRegistry.register_resolver(my_resolver)
            # Optional: parameter resolvers (transform config values)
            # ClassRegistry.register_param_resolver(my_param_resolver)

Package as an Entry Point
-------------------------

**pyproject.toml**

.. code-block:: toml

    [project.entry-points."semantiva.extensions"]
    my-domain = "my_pkg.ext:MyDomainExtension"

Loading Extensions
------------------

From YAML:

.. code-block:: yaml

    extensions: ["my-domain"]

or:

.. code-block:: yaml

    pipeline:
      extensions: ["my-domain"]

From Python (deterministic loading):

.. code-block:: python

    from semantiva.registry import load_extensions

    load_extensions(["my-domain"])  # Raises RuntimeError if hooks are missing

The loader sorts requested extensions, imports each module at most once, and
falls back to entry points under ``semantiva.extensions``. Extensions must
expose either a ``SemantivaExtension`` subclass or a module-level
``register()`` callable. Failure to provide hooks raises a ``RuntimeError``
describing the missing integration.

Authoring Reminders
--------------------

- Use **DataOperation**/**DataProbe** for processing.
- **Probes** are read-only: declare **only** ``input_data_type``; do not mutate context.
- Use **DataSource**/**DataSink** for I/O; **ContextProcessor** for domain context.
- Run ``semantiva dev lint`` to verify contract compliance.

