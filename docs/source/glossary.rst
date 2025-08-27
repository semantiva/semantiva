Glossary
========

.. glossary::

   Pipeline
     The ordered execution of factory-generated nodes wrapping processors.

   Node
     A factory-generated wrapper (users do not subclass nodes).

   Processor
     A single-responsibility unit of computation (DataOperation, DataProbe, IO, ContextProcessor).

   DataType
     A typed wrapper for domain data; used to enforce contracts between operations.

   DataOperation
     A processor that transforms one typed ``data`` value into another within a Payload.

   Context
     Execution key/value store with safe mutation (required/created/suppressed keys).

   Payload
     The envelope passed between nodes during execution, carrying both
     ``data`` (typed value) and ``context`` (metadata dictionary with
     required/created/suppressed keys). Pipelines always return a Payload
     when executed.

   Resolver
     A mechanism that rewrites or resolves parts of a configuration during spec parsing.

   Class Resolver
     Resolves a ``processor`` reference to an importable class (usually by FQCN).

   Parameter Resolver
     Transforms parameter maps (e.g., ``slicer:``, ``rename:``, ``delete:``, ``model:``).

   Studio Viewer
     Read-only UI for YAML pipeline visualization.

See also
--------

For examples of resolver usage, see :ref:`objects-in-pipeline-configurations`
and the *Resolvers Overview* in :doc:`registry_and_extensions`.
