Trace ↔ Graph Alignment
=======================

This page explains how **Step Evidence Records (SER)** align with the
**GraphV1** pipeline graph. The canonical mapping allows tools to reconstruct
execution topology solely from SER files.

Node Identity
-------------

* Every pipeline node is assigned a deterministic ``node_uuid`` by the
  GraphV1 builder.
* The same ``node_uuid`` appears:
  * In the canonical spec (``canonical_spec.nodes[*].node_uuid``).
  * In each SER record as ``ids.node_id``.

  **Rule:** Consumers must always join SER data to the graph using ``node_uuid``.

SER Output
----------

SER records contain minimal information. Optional fields may be supplied by the
runtime and consumers should ignore unknown fields gracefully.

Pipeline & Run Identity
-----------------------

* ``pipeline_id``: deterministic hash of the canonical spec.
* ``run_id``: unique per execution.
* Both appear in ``pipeline_start`` records and in the ``ids`` of each SER.

Trace → Graph Usage
-------------------

To recreate the execution graph from SER files:

1. Read ``pipeline_start`` to obtain the canonical graph.
2. For each SER record, use ``ids.node_id`` and ``topology.upstream`` to build edges.
3. Combine with per-step information from ``action``, ``io_delta`` and ``checks``.

