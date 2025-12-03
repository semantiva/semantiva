Architecture overview
=====================

.. admonition:: Who this is for

   This page is for **architects and system designers** who need a concise
   overview of how Semantiva fits into a wider system.

   It assumes you are comfortable with pipelines and components
   (:doc:`../personas/pipeline_users`, :doc:`../personas/framework_developers`)
   and have skimmed :doc:`../inspection`.

Execution core
--------------

Semantiva executes **directed graphs of nodes** built from YAML configuration.
Nodes wrap **processors** that handle either the **data channel** or the
**context channel**:

- The data channel carries the primary payload data.
- The context channel (``payload.context``) carries metadata and intermediate
  values, validated via observers.
- Nodes are instantiated by factories; processors remain stateless and
  reference types via ``input_data_type`` / ``output_data_type`` declarations.

The execution engine compiles YAML into a :term:`Graph (GraphV1)`, assigns
stable semantic identifiers, and drives each node while keeping data/context
separated for traceability. See :doc:`../pipeline` for pipeline semantics.

Inspection & trace stack
------------------------

Semantiva treats inspection and tracing as first-class citizens:

- :doc:`../inspection` builds a configuration-only, deterministic payload for
  CLI and UI consumers.
- :doc:`../ser` describes the Semantic Execution Record (SER); the full schema
  is in :doc:`../schema_semantic_execution_record_v1`.
- Runtime emits a JSONL :doc:`../trace_stream_v1` with SERs and lifecycle
  records; :doc:`../trace_aggregator_v1` provides aggregation and completeness
  checks.
- Graph alignment guidance lives in :doc:`../trace_graph_alignment`.
- Run-space orchestration surfaces in :doc:`../run_space` and
  :doc:`../run_space_lifecycle`.

Contracts & invariants
----------------------

Contracts are **machine-checkable architecture rules** enforced by linting
(:doc:`../contracts`). They codify processor invariants (e.g., probes are
read-only, context writes are declared) and trace identity expectations. The
SVA catalog remains authoritative; this page is a map, not a substitute.

Extension & integration points
------------------------------

Semantiva is extensible through **component families** and **registries**:

- Author processors following :doc:`../creating_components`; register them via
  extensions (:doc:`../extensions`).
- The registry model and namespacing are covered in
  :doc:`registry`.
- Context processing internals and observer wiring are detailed in
  :doc:`context_processing`.
- Pipeline schema and validation rules live in :doc:`pipeline_schema`.
- Execution wiring and transports are outlined in :doc:`../execution`.
- Visual inspection and debugging are supported by :doc:`../studio_viewer`.

Related persona
---------------

For role-oriented guidance and learning paths, see
:doc:`../personas/architects_system_designers`.
