Tracing
=======

Semantiva offers an optional tracing facility that captures minimal execution
records for each pipeline run. Tracing is disabled by default and incurs no
runtime cost unless explicitly enabled.

The trace system implements v1 contracts ensuring forward compatibility and
providing optional output-only semantic summaries with configurable detail levels.

GraphV1 & Pipeline Identity
---------------------------

The core provides a canonical graph builder which returns *GraphV1*. From this
specification a deterministic ``PipelineId`` is derived. Each node in the graph
receives a stable ``node_uuid`` that is reused across YAML, dictionaries or
programmatic pipeline construction.

Record Envelopes
----------------

Every record carries ``schema_version: 1`` and consumers must switch on the
``type`` field while ignoring unknown fields. Reserved fields such as
``plan_id`` and ``plan_epoch`` default to ``null`` and ``0`` respectively.

Trace v1 node events include optional fields for output-only semantic summaries:
- ``out_data_repr``: Human-readable representation (when detail≥repr)
- ``out_data_hash``: Content hash for change detection (when detail≥hash)  
- ``post_context_hash``: Post-execution context fingerprint (when detail≥hash)

Example ``pipeline_start`` record::

    {
      "type": "pipeline_start",
      "schema_version": 1,
      "pipeline_id": "plid-sha256-...",
      "run_id": "run-...",
      "canonical_spec": {"version": 1, "nodes": [...], "edges": [...]},
      "meta": {"num_nodes": 5},
      "plan_id": null,
      "plan_epoch": 0
    }

Node events appear before and after execution (or once with ``error``). The
``node_uuid`` within each event aligns with ``canonical_spec.nodes[*].node_uuid``.

CLI Usage
---------

Tracing is enabled via the CLI using ``--trace-driver`` and ``--trace-output``::

    semantiva run pipeline.yaml --trace-driver jsonl --trace-output traces/

The ``--trace-detail`` flag controls semantic summary inclusion:
- ``timings``: Node execution timing only (default)
- ``hash``: Add output and context hashes for change detection
- ``repr``: Add human-readable output representations  
- ``all``: Include all available detail levels

When the output path is a directory, files are created using the pattern
``{YYYYMMDD-HHMMSS}_{RUNID}.jsonl``. For custom drivers the ``pythonpath``
option can be used to import a driver class.

See also :doc:`trace_graph_alignment` for the contract between trace records and
GraphV1.

Public API Surface  
------------------

- Core Types: :py:mod:`semantiva.trace.model`
- JSONL Driver: :py:mod:`semantiva.trace.drivers.jsonl`

Autodoc
-------

.. automodule:: semantiva.trace.model
   :members:
   :undoc-members:

.. automodule:: semantiva.trace.drivers.jsonl
   :members:
   :undoc-members:
