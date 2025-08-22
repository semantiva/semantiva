Canonical Graph Builder
=======================

The ``semantiva.pipeline.graph_builder`` module normalizes a pipeline definition
(from YAML, dictionaries or an existing :class:`~semantiva.pipeline.Pipeline`)
into a canonical *GraphV1* representation. Each node receives a deterministic
``node_uuid`` and the entire graph hashes to a ``PipelineId`` using SHA-256.

GraphV1 guarantees:

* **version: 1** in all canonical specifications
* **Deterministic node identities**: UUIDv5 derived from canonical fields (role, FQCN, params, ports)
* **Linear chain edges** for demo pipelines (ODO will extend topology later without breaking node identities)
* **Stable PipelineId**: "plid-" + sha256(canonical_spec JSON)

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
