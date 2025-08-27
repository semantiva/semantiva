Semantiva Studio Viewer (Read-Only)
===================================

- Visualizes YAML pipelines (DAG with data/context/IO channels + **configuration column**)
- Node detail panel, static parameter display, error visualization
- No runtime state

Usage
-----

1) Prepare YAML (see :doc:`getting_started`)
2) Open in Studio Viewer (see project README or viewer repository)

Correlating Traces with the Viewer
----------------------------------

Semantiva Studio Viewer renders the canonical graph. To correlate with traces:

* Open the pipeline YAML in the Viewer (see :doc:`getting_started`).
* Select a node to reveal its details (including the stable **node_uuid**).
* In your trace file, filter node events by the same ``node_uuid`` to review
  timing, summaries, or errors for that node.

See :doc:`trace_graph_alignment` for identity alignment guarantees.

Limitations
-----------

- Read-only by design
- No data-dependent or runtime-dependent information
