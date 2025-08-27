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

CLI Usage
---------

Options & Drivers
~~~~~~~~~~~~~~~~~

Tracing is disabled by default. Enable it with a driver and output path.

.. _trace-detail-and-format:

**CLI options**

+---------------------+-----------------------+---------------------------+-----------------------------------------------------------+
| Option              | Type                  | Default                   | Description                                               |
+=====================+=======================+===========================+===========================================================+
| ``--trace-driver``  | ``jsonl`` or FQCN     | *(required to enable)*    | Select the trace driver. ``jsonl`` is the built-in        |
|                     |                       |                           | line-oriented JSON driver (Trace v1). Custom drivers      |
|                     |                       |                           | can be provided via fully-qualified class name (FQCN).    |
+---------------------+-----------------------+---------------------------+-----------------------------------------------------------+
| ``--trace-output``  | path (dir or file)    | none                      | Output destination. If a **directory**, the driver        |
|                     |                       |                           | creates a file using the naming pattern below.            |
+---------------------+-----------------------+---------------------------+-----------------------------------------------------------+
| ``--trace-detail``  | csv of flags          | ``hash``                  | Controls optional summary fields on node events.          |
|                     | (``hash``, ``repr``,  |                           | See :ref:`trace-detail-matrix`.                           |
|                     | ``context``, ``all``) |                           |                                                           |
+---------------------+-----------------------+---------------------------+-----------------------------------------------------------+

**Output naming (JSONL driver)**

When ``--trace-output`` is a directory, files are created using:

``{YYYYMMDD-HHMMSS}_{RUNID}.jsonl``

The JSONL driver writes **pretty-printed JSON** with indentation and sorted keys for readability (one event per block).

.. note::

   The JSONL driver ignores any "compact/pretty" toggle; it always writes
   pretty-printed JSON blocks (Trace v1).

Examples
~~~~~~~~

.. code-block:: bash

   # Minimal tracing (hash-only summaries)
   semantiva run hello_pipeline.yaml \
     --trace-driver jsonl \
     --trace-output traces/

   # All optional summaries (repr + hash + post-context repr)
   semantiva run hello_pipeline.yaml \
     --trace-driver jsonl \
     --trace-output traces/ \
     --trace-detail all

Hello, Trace
------------

.. code-block:: bash

   semantiva run hello_pipeline.yaml \
     --trace-driver jsonl \
     --trace-output traces/

Sample (truncated):

.. code-block:: javascript

   {
     "type": "pipeline_start",
     "schema_version": 1,
     "pipeline_id": "plid-...",
     "run_id": "run-...",
     "event_time_utc": "...",
     "canonical_spec": {"version": 1, "nodes": [...], "edges": [...]},
     "meta": {"num_nodes": 3},
     "plan_id": null,
     "plan_epoch": 0
   }

.. code-block:: javascript

   {
     "type": "node",
     "schema_version": 1,
     "phase": "done",
     "event_time_utc": "...",
     "address": {"pipeline_run_id": "run-...", "pipeline_id": "plid-...", "node_uuid": "..."},
     "t_wall": 0.03,
     "t_cpu": 0.02,
     "out_data_hash": "sha256-...",
     "post_context_hash": "sha256-..."
   }

Record Schema (Trace v1)
------------------------

Semantiva emits structured records (Trace v1). Reserved fields are included for
forward compatibility.

Pipeline start
~~~~~~~~~~~~~~

.. code-block:: javascript

   {
     "type": "pipeline_start",
     "schema_version": 1,
     "pipeline_id": "plid-033c3704...300e",
     "run_id": "run-12c844d9...c225f",
     "event_time_utc": "2025-08-26T09:10:11.123456Z",
     "canonical_spec": {"version": 1, "nodes": [...], "edges": [...]},
     "meta": {"num_nodes": 3},
     "plan_id": null,
     "plan_epoch": 0
   }

Node events
~~~~~~~~~~~

Each node event includes an address with ``pipeline_id``, ``pipeline_run_id`` and ``node_uuid``.

**start**

.. code-block:: javascript

   {
     "type": "node",
     "schema_version": 1,
     "phase": "start",
     "event_time_utc": "2025-08-26T09:10:12.000123Z",
     "address": {"pipeline_run_id": "run-12c844d9...c225f",
                 "pipeline_id": "plid-033c3704...300e",
                 "node_uuid": "2bd52eb9-9556-5663-b633-b69c9418f3ab"}
   }

**done** (with optional summaries controlled by ``--trace-detail``)

.. code-block:: javascript

   {
     "type": "node",
     "schema_version": 1,
     "phase": "done",
     "event_time_utc": "2025-08-26T09:10:12.123789Z",
     "address": {"pipeline_run_id": "run-12c844d9...c225f",
                 "pipeline_id": "plid-033c3704...300e",
                 "node_uuid": "eb3e87c0-97b7-5097-8214-b53b4ba0fd6e"},
     "t_wall": 0.12,
     "t_cpu": 0.11,
     "out_data_hash": "sha256-7240...",          // when "hash"
     "out_data_repr": "Float(2.0)",              // when "repr"
     "post_context_hash": "sha256-628e...",      // when "hash"
     "post_context_repr": "step=7,mode=eval"     // when "repr" + "context"
   }

**error**

.. code-block:: javascript

   {
     "type": "node",
     "schema_version": 1,
     "phase": "error",
     "event_time_utc": "2025-08-26T09:10:12.234567Z",
     "address": {"pipeline_run_id": "run-12c844d9...c225f",
                 "pipeline_id": "plid-033c3704...300e",
                 "node_uuid": "eb3e87c0-97b7-5097-8214-b53b4ba0fd6e"},
     "t_wall": 0.05,
     "t_cpu": 0.04,
     "error_type": "ValueError",
     "error_msg": "can't multiply sequence by non-int of type 'float'"
   }

Reserved fields
~~~~~~~~~~~~~~~

* ``plan_id``: always ``null`` in v1 (reserved).
* ``plan_epoch``: always ``0`` in v1 (reserved).

See also :doc:`trace_graph_alignment` for identity alignment details.

.. _trace-detail-matrix:

Detail Levels (Summary Fields)
------------------------------

The following flags control **optional** summary fields on node ``done`` events.

+-----------+----------------------+-----------------------------------------------+
| Flag      | Affects              | Emitted fields                                |
+===========+======================+===============================================+
| ``hash``  | data & context       | ``out_data_hash``, ``post_context_hash``      |
+-----------+----------------------+-----------------------------------------------+
| ``repr``  | data                 | ``out_data_repr``                             |
+-----------+----------------------+-----------------------------------------------+
| ``context`` | context (with repr)| ``post_context_repr`` (only with ``repr``)    |
+-----------+----------------------+-----------------------------------------------+
| ``all``   | all of the above     | ``out_data_hash``, ``post_context_hash``,     |
|           |                      | ``out_data_repr``, ``post_context_repr``      |
+-----------+----------------------+-----------------------------------------------+

Timing metrics
~~~~~~~~~~~~~~

Execution timing (``t_wall``, ``t_cpu``) is always recorded on node events and
does not depend on the detail flags.

.. _pretty-vs-compact-json:

Output Format & Naming
----------------------

**JSONL driver**: emits one event per **pretty-printed** JSON block with indentation
and sorted keys (human-friendly). The ``--trace-output`` directory naming pattern is:

``{YYYYMMDD-HHMMSS}_{RUNID}.jsonl``

Other drivers may support different formatting. For JSONL, compact/pretty toggles
are not applicable.

Consuming Traces Programmatically
---------------------------------

Example: read a JSONL file, group events by ``node_uuid``, and compute simple aggregates.

.. code-block:: python

   import json
   from collections import defaultdict

   def read_trace_jsonl(path):
       events = []
       with open(path, "r", encoding="utf-8") as f:
           buf = []
           for line in f:
               # JSONL (pretty blocks): detect record boundaries by blank lines
               if line.strip():
                   buf.append(line)
                   continue
               if buf:
                   events.append(json.loads("".join(buf)))
                   buf.clear()
           if buf:
               events.append(json.loads("".join(buf)))
       return events

   def summarize_by_node(events):
       by_node = defaultdict(list)
       for ev in events:
           if ev.get("type") == "node":
               by_node[ev["address"]["node_uuid"]].append(ev)
       summary = {}
       for node_uuid, evs in by_node.items():
           dones = [e for e in evs if e.get("phase") == "done"]
           errs  = [e for e in evs if e.get("phase") == "error"]
           t_wall = sum(e.get("t_wall", 0.0) for e in dones)
           t_cpu  = sum(e.get("t_cpu", 0.0) for e in dones)
           summary[node_uuid] = {"runs": len(dones),
                                 "errors": len(errs),
                                 "t_wall_total": t_wall,
                                 "t_cpu_total": t_cpu}
       return summary

   events = read_trace_jsonl("traces/20250826-091011_run-12c8....jsonl")
   summary = summarize_by_node(events)
   print(summary)

See also :doc:`trace_graph_alignment` for how to join traces to GraphV1 by ``node_uuid``.

Troubleshooting
---------------

**“Why do I see ``null`` or missing fields?”**

* ``plan_id`` is reserved → always ``null`` in Trace v1.
* ``plan_epoch`` is reserved → always ``0`` in Trace v1.
* Optional summaries (``out_data_repr``, ``out_data_hash``,
  ``post_context_hash``, ``post_context_repr``) are only emitted if
  enabled via ``--trace-detail`` (see :ref:`trace-detail-matrix`).
* Drivers and policies may omit large/unsafe representations by design.

**Checklist**

* Re-run with ``--trace-detail all`` to confirm summaries appear.
* Verify you are opening the **latest** file in the output directory.
* Inspect corresponding identities on :doc:`trace_graph_alignment`
  to ensure you’re looking at the correct ``node_uuid`` and run.

Performance & Cost Tuning
-------------------------

Baseline overhead is low (one record per node event). Additional cost is driven by:

* **repr** – constructing readable data/context representations may be expensive.
* **hash** – content hashing scales with output size.
* **I/O** – writing larger events increases disk/network cost.

Recommendations:

* **Production**: use ``--trace-detail hash`` for change detection with minimal overhead.
* **Debugging**: temporarily switch to ``--trace-detail all`` to capture human-readable context.
* Avoid ``repr`` on massive structures, or cap your processors' repr length.

Privacy & Redaction
-------------------

Caution: ``repr`` summaries may include sensitive data (PII, secrets).

* Prefer ``--trace-detail hash`` in regulated environments.
* Limit ``repr`` usage to development sessions or redacted objects.
* Avoid including secrets in context; store references/tokens elsewhere.
* Ensure trace files are stored under appropriate access controls.

Public API Surface
------------------

Stable modules for Trace v1:

- Core Types: :py:mod:`semantiva.trace.model`
- JSONL Driver: :py:mod:`semantiva.trace.drivers.jsonl`

.. note::

   Only the modules above are considered stable public surface for Trace v1.
   Internal helpers and private modules are subject to change without notice.

Autodoc
-------

.. automodule:: semantiva.trace.model
   :members:
   :undoc-members:

.. automodule:: semantiva.trace.drivers.jsonl
   :members:
   :undoc-members:

