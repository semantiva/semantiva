Glossary
========

.. glossary::

   Class Resolver
     Resolves a ``processor`` reference (typically via Fully Qualified Class Name) to an
     importable Python class in the current environment.

   Context
     Execution key/value store with safe mutation (required/created/suppressed keys).

   DataOperation
     A processor that transforms one typed ``data`` value into another within a Payload.

   DataType
     A typed wrapper for domain data; used to enforce contracts between operations.

   GraphV1
     The canonical, normalized graph representation constructed from a pipeline spec
     (e.g., YAML). GraphV1 guarantees deterministic identity for nodes and pipelines.
     See :doc:`graph`.

   Node
     A factory-generated wrapper (users do not subclass nodes).

   Parameter Resolver
     Transforms parameter maps, e.g.,

     - ``slicer:`` — reference/slice a value from context/parameters
     - ``rename:`` — rename keys according to a mapping
     - ``delete:`` — remove keys or subtrees
     - ``model:`` — wrap a live object behind a serializable descriptor

   Payload
     The envelope passed between nodes during execution, carrying both **data**
     (a typed value, subclass of ``BaseDataType``) and **context** (metadata dict
     with required/created/suppressed keys). Pipelines return a Payload on ``process``.

   Pipeline
     The ordered execution of factory-generated nodes wrapping processors.

   PipelineId
     Deterministic identifier for a pipeline derived from its canonical spec
     (formatting changes do not affect it). Appears in inspection output and trace records.

   Processor
     A single-responsibility unit of computation (DataOperation, DataProbe, IO, ContextProcessor).

   Resolver
     A mechanism that rewrites or resolves parts of a configuration during spec parsing
     or realization. Examples include parameter slicing, renaming, and object modeling.

   Trace Driver
     A pluggable sink that writes trace events. In 0.5.0, the built-in driver is
     ``jsonl`` (pretty-printed JSON blocks). See :doc:`tracing`.

   node_uuid
     Positional, stable identifier for a node within GraphV1. Used to align inspection,
     tracing, and Viewer node details. See :doc:`graph`.

   Context Observer
     Mediates context writes/deletes from processors to the active context.

   Validating Observer
     Observer that enforces declared created/suppressed keys.

   Required keys
     Keys that must exist before the processor runs.

   Created keys
     Keys a processor may create/update.

   Suppressed keys
     Keys a processor may delete.

   Studio Viewer
     Read-only UI for YAML pipeline visualization.

Conventions
-----------

Use these terms and casing consistently:

* **Payload**, **GraphV1**, **PipelineId**, **Trace Driver** (caps as shown)
* **node_uuid** (monospace when referencing the exact field name)
* Use :term:`Payload` on first mention in a section; likewise for other terms.
* Use monospace for field names: ``node_uuid``, ``pipeline_id``, ``t_wall``.
* Use singular for concept names (e.g., "a :term:`Payload`", not "payloads" in headings).

See also
--------

For examples of resolver usage, see :ref:`objects-in-pipeline-configurations`
and the *Resolvers Overview* in :doc:`extensions`.

