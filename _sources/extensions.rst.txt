Extending Semantiva (Registries & Extensions)
=============================================

This document provides a comprehensive guide for creating and using Semantiva extensions. Extensions enable domain-specific functionality by registering processors, execution components, and custom resolvers.

Overview
--------

Semantiva extensions are modular components that extend the core framework with domain-specific capabilities. Extensions can provide:

- Custom data types and operations
- Domain-specific processors and probes  
- Custom data sources and sinks
- Execution components (orchestrators, executors, transports)
- Custom name and parameter resolvers

Public API Contract
-------------------

Extensions interact with Semantiva through the following public APIs:

Processor Registration
~~~~~~~~~~~~~~~~~~~~~~

Register modules containing processor classes:

.. code-block:: python

    from semantiva.registry.processor_registry import ProcessorRegistry
    
    ProcessorRegistry.register_modules([
        "your_package.operations",
        "your_package.probes",
        "your_package.data_io"  
    ])

Execution Components
~~~~~~~~~~~~~~~~~~~~

Register custom execution components:

.. code-block:: python

    from semantiva.execution.component_registry import ExecutionComponentRegistry as ECR
    
    ECR.register_orchestrator("custom-orch", CustomOrchestrator)
    ECR.register_executor("custom-exec", CustomExecutor)  
    ECR.register_transport("custom-transport", CustomTransport)

Parameter Resolvers
~~~~~~~~~~~~~~~~~~~

Register custom parameter transformation functions:

.. code-block:: python

    from semantiva.registry.parameter_resolver_registry import ParameterResolverRegistry
    import os

    def my_param_resolver(value):
        if isinstance(value, str) and value.startswith("myenv:"):
            return os.environ.get(value.split(":",1)[1], ""), True
        return value, False
    
    ParameterResolverRegistry.register_resolver("myenv", my_param_resolver)

Name Resolvers  
~~~~~~~~~~~~~~

Register custom name-based processor resolvers:

.. code-block:: python

    from semantiva.registry.name_resolver_registry import NameResolverRegistry
    # Example mapping: "myprefix:multiply" -> a known processor class

    def my_name_resolver(value):
        if isinstance(value, str) and value == "myprefix:multiply":
            from semantiva.examples.test_utils import FloatMultiplyOperation
            return FloatMultiplyOperation
        return None

    NameResolverRegistry.register_resolver("myprefix:", my_name_resolver)

Implement an Extension
----------------------
Subclass ``SemantivaExtension`` and implement ``register()``. When registering
execution-layer integrations (orchestrators, executors, transports), call the
Execution Component Registry (ECR):

.. code-block:: python

    from semantiva.execution.component_registry import ExecutionComponentRegistry as ECR
    from semantiva.registry import (
        SemantivaExtension,
        ProcessorRegistry,
        NameResolverRegistry,
        ParameterResolverRegistry,
    )

    class MyDomainExtension(SemantivaExtension):
        def register(self) -> None:
            ProcessorRegistry.register_modules([
                "my_pkg.ops",      # DataOperation/DataProbe subclasses
                "my_pkg.io",       # DataSource/DataSink
                "my_pkg.context",  # ContextProcessor
            ])
            # Register execution components
            ECR.register_orchestrator("my-local", MyLocalOrchestrator)

            # Optional: custom class-name resolvers (e.g., "rename:Old:New")
            # NameResolverRegistry.register_resolver("prefix:", my_resolver)
            # Optional: parameter resolvers (transform config values)
            # ParameterResolverRegistry.register_resolver("my_param_resolver", my_param_resolver)

Migration Examples
------------------

For extensions migrating from legacy APIs, here are drop-in migration patterns:

Semantiva AutoDrive Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.registry import SemantivaExtension
    from semantiva.registry.processor_registry import ProcessorRegistry

    class AutoDriveExtension(SemantivaExtension):
        def register(self) -> None:
            ProcessorRegistry.register_modules([
                "semantiva_autodrive.data_io",
                "semantiva_autodrive.processing",
                "semantiva_autodrive.probes.probes",
                "semantiva_autodrive.context_processors.processors",
            ])

Semantiva Chain Extension
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.registry import SemantivaExtension
    from semantiva.registry.processor_registry import ProcessorRegistry

    class SemantivaChain(SemantivaExtension):
        name = "semantiva-chain"
        version = "0.1.0"

        def register(self) -> None:
            ProcessorRegistry.register_modules([
                "semantiva_chain.core",
                "semantiva_chain.datatypes", 
                "semantiva_chain.llm",
            ])

Template Extension
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.registry import SemantivaExtension
    from semantiva.registry.processor_registry import ProcessorRegistry

    class TemplateExtension(SemantivaExtension):
        def register(self) -> None:
            ProcessorRegistry.register_modules([
                "template_extension.data_types",
                "template_extension.operations",
                "template_extension.probes",
                "template_extension.data_io",
                "template_extension.context_processors",
            ])

Extension with Execution Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.registry import SemantivaExtension
    from semantiva.registry.processor_registry import ProcessorRegistry
    from semantiva.execution.component_registry import ExecutionComponentRegistry as ECR

    class VendorExtension(SemantivaExtension):
        def register(self) -> None:
            ProcessorRegistry.register_modules([
                "vendor_extension.processors"
            ])
            ECR.register_executor("vendor-ray", VendorRayExecutor)
            ECR.register_transport("vendor-queue", VendorRayTransport) 
            ECR.register_orchestrator("vendor-orch", VendorOrchestrator)

Package as an Entry Point
-------------------------

**pyproject.toml**

.. code-block:: toml

    [project.entry-points."semantiva.extensions"]
    my-domain = "my_pkg.ext:MyDomainExtension"

Built-in Extensions
-------------------

Semantiva Examples Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``semantiva-examples`` extension provides Float-based processors used in documentation and testing:

.. code-block:: yaml

    extensions: ["semantiva-examples"]
    
    pipeline:
      nodes:
        - processor: FloatValueDataSource
          parameters: { value: 2.0 }
        - processor: FloatMultiplyOperation
          parameters: { factor: 3.0 }

This extension includes:

- ``FloatDataType`` and ``FloatDataCollection``
- Float arithmetic operations (``FloatAddOperation``, ``FloatMultiplyOperation``, etc.)
- Float data sources and sinks (``FloatValueDataSource``, ``FloatTxtFileSaver``)
- Float probes for inspection (``FloatBasicProbe``, ``FloatCollectValueProbe``)

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
- Extensions should be idempotent: ``register()`` can be called multiple times safely.
- Organize processors into logical modules (operations, probes, data_io, etc.).
- Handle registration errors gracefully and provide informative error messages.
- Test extensions both in isolation and integrated with the core framework.
- Run ``semantiva dev lint`` to verify contract compliance.

Thread Safety
--------------

Extension registration should be thread-safe. The ``register()`` method may be called concurrently in multi-threaded environments.

