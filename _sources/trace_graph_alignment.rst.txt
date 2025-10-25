Trace ↔ Graph Alignment
=======================

This page explains how **Semantic Execution Records (SER)** align with the
**GraphV1** pipeline graph. The canonical mapping allows tools to reconstruct
execution topology solely from SER files.

Node Identity
-------------

* Every pipeline node is assigned a deterministic ``node_uuid`` by the
  GraphV1 builder.
* The same ``node_uuid`` appears:
  * In the canonical spec (``pipeline_spec_canonical.nodes[*].node_uuid``).
  * In each SER record as ``identity.node_id``.

  **Rule:** Consumers must always join SER data to the graph using ``node_uuid``.

SER Output
----------

SER records contain minimal information. Optional fields may be supplied by the
runtime and consumers should ignore unknown fields gracefully.

Pipeline & Run Identity
-----------------------

* ``pipeline_id``: deterministic hash of the canonical spec.
* ``run_id``: unique per execution.
* Both appear in ``pipeline_start`` records and in the ``identity`` of each SER.

Trace → Graph Usage
-------------------

To recreate the execution graph from SER files:

1. Read ``pipeline_start`` records (``record_type='pipeline_start'``) to obtain the canonical graph from ``pipeline_spec_canonical``.
2. For each SER record, use ``identity.node_id`` and ``dependencies.upstream`` to build edges.
3. Combine with per-step information from ``processor``, ``context_delta`` and ``assertions``.

The canonical graph exposes ``processor_ref`` (FQCN); SER mirrors this as ``processor.ref``.

