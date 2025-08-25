Trace ↔ Graph Alignment
=======================

This page explains how **Semantiva Trace Records** and the **GraphV1 pipeline graph** align.
It defines the canonical contract that **all consumers must rely on** - whether using
Semantiva Studio Viewer or building custom tooling.

Trace v1 extends the core contract with optional output-only semantic summaries while
maintaining backward compatibility for all existing consumers.

Node Identity
-------------

* Every pipeline node is assigned a **deterministic ``node_uuid``** by the core **GraphV1 builder**.
* The same ``node_uuid`` appears:
  * In the pipeline’s canonical spec (``canonical_spec.nodes[*].node_uuid``).
  * In every ``NodeTraceEvent.address.node_uuid`` inside trace JSONL.
* This guarantees stable addressing across:
  * YAML vs dict vs programmatic definitions.
  * Dual-channel (data + context) pipelines.
  * Future multi-channel / ODO pipelines.

  **Rule:** Consumers must always join trace data to the graph using ``node_uuid``.
  

Trace v1 Output Summaries
-------------------------

* **Optional fields** in node events provide semantic summaries without breaking compatibility:
  * ``out_data_repr``: Human-readable output representation (detail≥repr)
  * ``out_data_hash``: Content hash for change detection (detail≥hash)
  * ``post_context_hash``: Post-execution context fingerprint (detail≥hash)
* These fields are **null** when not requested via ``--trace-detail`` and are omitted from JSON.
* Consumers should handle missing/null fields gracefully.

Pipeline & Run Identity
-----------------------

* **PipelineId**: deterministic hash of the canonical spec; identical for equivalent graphs.
* **PipelineRunId**: unique per execution (UUIDv7).
* Both appear in ``pipeline_start`` records and can be cross-checked against the graph spec.

Trace → Graph Usage
-------------------

1. **Load canonical graph** using ``semantiva.pipeline.graph_builder.build_graph(...)``.
2. **Load trace JSONL** and index events by ``node_uuid``.
3. Join per-node aggregates/events to the graph model via ``node_uuid``.
4. Use run/pipeline IDs for sanity checks and multi-run grouping.

Forward Compatibility
---------------------

* Reserved fields (``plan_id``, ``plan_epoch``) exist in Trace v1 envelopes but are always ``null`` / ``0``.
* Trace v1 summary fields are optional and backward compatible.
* ODO extensions (dynamic topology) will remain backward compatible:
  * New events will include ``node_uuid`` consistently.
  * Existing consumers that ignore unknown fields will continue to work.

Consumer Guidance
-----------------

* Always switch on ``record["type"]``.
* Ignore unknown fields.
* Handle missing/null summary fields gracefully.
* Use ``node_uuid`` for node alignment.
* Use ``pipeline_id`` + ``run_id`` for run alignment.

Why UUIDs, not indices?
-----------------------

* Node indices can drift (YAML order, insertion, adaptation).
* UUIDs are deterministic from spec → stable over time.
* Simplifies joining trace + graph, even under future multi-channel DAGs.
