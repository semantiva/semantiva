Canonical Graph Builder
=======================

The :py:mod:`semantiva.pipeline.graph_builder` module normalizes a pipeline definition
(from YAML, dictionaries or an existing ``Pipeline``)
into a canonical :term:`GraphV1` representation. Each node receives a deterministic
:term:`node_uuid`, and the canonical graph feeds Semantiva's identity stack
(:ref:`identity-quick-map`).

Graph and Identity
------------------

When Semantiva loads a YAML pipeline, it is converted into a canonical ``GraphV1``.
From this graph Semantiva derives stable identifiers used across inspection,
run-space planning, and runtime traces (see :doc:`identity_cheatsheet`):

* ``node_uuid`` - positional identifier for each declared node.
* ``node_semantic_id`` - captures preprocessor semantics for nodes that use
  ``derive`` blocks (e.g., parameter sweeps).
* **Semantic ID** (``plsemid-…``) - the pipeline meaning hash computed from the
  canonical graph and node semantics.

Runtime identifiers such as ``plid-…`` (execution container) are derived later
during execution; they reference the same canonical graph but are covered in
the :doc:`identity_cheatsheet` quick map and :doc:`trace_stream_v1`.

GraphV1 guarantees:

* **version: 1** in all canonical specifications
* **Deterministic node identities**: UUIDv5 derived from canonical fields (role, FQCN, params, ports)
* **Linear chain edges** for demo pipelines (ODO will extend topology later without breaking node identities)
* **Stable PipelineId**: "plid-" + sha256(canonical_spec JSON)

.. note::
   To avoid identity churn, :term:`derive` blocks (e.g., ``derive.parameter_sweep``)
   are **not** hashed into the node UUID. Only the resolved processor class and the
   **effective** parameter map (after preprocessing/merging) participate. Semantic
   changes introduced by preprocessors are tracked separately via
   ``node_semantic_id`` and rolled into the pipeline Semantic ID.

Example::

    from semantiva.pipeline import build_graph, compute_pipeline_id
    graph = build_graph("tests/simple_pipeline.yaml")
    pipeline_id = compute_pipeline_id(graph)
    print(pipeline_id)

Canonical fields that feed UUIDv5:
- role: Node's semantic role in the pipeline
- FQCN: Fully qualified class name of the processor
- params: Shallow parameter mapping (sorted keys)
- ports: Declared input/output port specifications

See :doc:`trace_graph_alignment` for how this graph aligns with tracing.

See also
--------

For how these identities appear in inspection outputs and error messages,
see :doc:`introspection_validation`.
