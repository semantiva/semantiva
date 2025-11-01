Canonical Graph Builder
=======================

The :py:mod:`semantiva.pipeline.graph_builder` module normalizes a pipeline definition
(from YAML, dictionaries or an existing :py:class:`semantiva.pipeline.pipeline.Pipeline`)
into a canonical :term:`GraphV1` representation. Each node receives a deterministic
:term:`node_uuid` and the entire graph hashes to a :term:`PipelineId` using SHA-256.

Graph and Identity
------------------

When Semantiva loads a YAML pipeline, it is converted into a canonical ``GraphV1``.
From this graph Semantiva derives stable identifiers:

* ``node_uuid`` - a positional identifier for each node.
* ``PipelineId`` - a deterministic identifier for the whole pipeline.

These identities are embedded in trace records and introspection outputs, ensuring
that pipelines can be compared, cached, and reproduced across environments.

GraphV1 guarantees:

* **version: 1** in all canonical specifications
* **Deterministic node identities**: UUIDv5 derived from canonical fields (role, FQCN, params, ports)
* **Linear chain edges** for demo pipelines (ODO will extend topology later without breaking node identities)
* **Stable PipelineId**: "plid-" + sha256(canonical_spec JSON)

.. note::
   To avoid identity churn, :term:`derive` blocks (e.g., ``derive.parameter_sweep``)
   are **not** hashed into the node UUID. Only the resolved processor class and the
   **effective** parameter map (after preprocessing/merging) participate.

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
