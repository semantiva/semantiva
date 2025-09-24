Semantiva Studio Viewer
=======================

The Studio Viewer renders pipeline YAML as an interactive diagram and can browse
installed components. It is **read-only** and designed for understanding,
review, and sharing.

Quick Start
-----------

**Visualize a pipeline**

.. code-block:: bash

   semantiva-studio-viewer serve-pipeline my_pipeline.yaml --port 8000
   # then open http://127.0.0.1:8000

**Export a standalone HTML**

.. code-block:: bash

   semantiva-studio-viewer export-pipeline my_pipeline.yaml --output pipeline_diagram.html
   # open pipeline_diagram.html in any browser, no server needed

**Browse components (if available)**

.. code-block:: bash

   semantiva-studio-viewer export-components --output semantiva_components.html
   semantiva-studio-viewer serve-components semantiva_components.ttl --port 8001
   # then open http://127.0.0.1:8001

See also:
* :doc:`pipeline` — how pipelines are defined and executed
* :doc:`tracing` — how to enable and read execution traces
* :doc:`extensions` — extending Semantiva and generating component sets

Modes & Controls
----------------

Viewer supports two modes:

* **Pipeline Visualization** — render a single pipeline YAML as an interactive DAG.
  Click a node to view its details (processor class, parameters, ports, identities).
* **Component Browser** — explore installed components (types, processors), organized
  by categories. Click items to view metadata and docstrings.

Basic controls (typical web-graph UX):

* **Pan**: click-drag canvas
* **Zoom**: mouse wheel / trackpad pinch
* **Select**: click a node
* **Focus**: double-click to center on a node (if supported)

Export & Share
--------------

Use ``export-pipeline`` to create a standalone HTML file that preserves pan/zoom
and click-to-inspect interactions. No server required.

.. code-block:: bash

   semantiva-studio-viewer export-pipeline my_pipeline.yaml --output pipeline_diagram.html

Share the HTML via email, internal portals, or attach it to reports. The export
does not contain live data or runtime state—only static metadata from the pipeline
definition and component docstrings.

.. _trace-inspection:

Trace Inspection
----------------

The Viewer renders the canonical graph. To inspect execution traces alongside
the diagram:

1. Open your pipeline YAML in the Viewer.
2. Click a node to see its details (including :term:`node_uuid`).
3. In your trace file (JSONL), filter node events by that ``node_uuid`` to review
   timings, summaries, or errors for the selected node.

See :doc:`tracing` for the record schema and :doc:`trace_graph_alignment` for identity guarantees.

.. _positional-binding-node_uuid:

Positional Binding (node_uuid)
------------------------------

Every node shown in the Viewer includes its positional identity, ``node_uuid``,
derived from the canonical GraphV1. This identity is:

* **Deterministic** for the same canonical spec (formatting changes do not affect it).
* **Comparable** across runs (join with trace events).
* **Stable** for documentation and audits.

For more on identity, see :doc:`graph`.

Limitations
-----------

* **Read-only**: the Viewer does not edit pipeline content.
* **No live runtime state**: values are not streamed into the diagram.

Troubleshooting
---------------

**Viewer doesn't start / port in use**  
Try a different port: ``--port 8002``

**Command not found**  
Ensure the package is installed in the active environment:
``pip install semantiva-studio-viewer``

**Blank diagram**  
Validate the YAML first: ``semantiva inspect pipeline.yaml --extended``.
Fix reported errors, then re-open in the Viewer.

**Component browser: where does the TTL come from?**  
Export it first:
``semantiva-studio-viewer export-components --output semantiva_components.ttl``.
See :doc:`extensions` for extension discovery/registration.

Inspection schema note (GUI)
----------------------------

Each node record now includes:

- ``invalid_parameters`` — list of ``{name, reason}``
- ``is_configuration_valid`` — false if invalid parameters exist

These allow the viewer to flag and annotate misconfigured nodes precisely.

Large Graphs
------------

For very large pipelines:

* Prefer generating a filtered/simplified YAML when inspecting specific areas.
* Use search/filter (if available) to focus on relevant processors.
* Export to HTML and share a focused subset for reviews.

See also
--------

* :doc:`pipeline` — from YAML to execution (and Payloads)
* :doc:`tracing` — record schema, detail flags, JSONL usage
* :doc:`graph` — GraphV1, node_uuid, PipelineId identities
* :doc:`extensions` — generating component sets
