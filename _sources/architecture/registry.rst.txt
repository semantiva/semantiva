Registry Bootstrap Profiles
===========================

The registry keeps track of modules, filesystem paths, and extension entry
points that declare Semantiva components. The **Registry v1** design introduces
``RegistryProfile`` to make that state explicit, portable, and reproducible.

Key Concepts
------------

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

.. code-block:: python

   from semantiva.registry.bootstrap import RegistryProfile, apply_profile, current_profile

   # Capture the current process state (defaults, modules, and paths)
   profile = current_profile()

   # Launch a distributed job with an explicit profile
   orchestrator.enqueue(pipeline_nodes, registry_profile=profile)

   # Rehydrate a profile in a worker or a separate process
   apply_profile(profile)

Idempotent Defaults
-------------------

``ClassRegistry.initialize_default_modules()`` no longer clears custom
resolvers when loading defaults, and built-in resolvers are installed once.
Calling the method repeatedly is safe and preserves any user-provided
resolvers.
