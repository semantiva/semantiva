Step Evidence Record (SER) v0 — draft
======================================

Semantiva records pipeline execution using the **Step Evidence Record (SER) v0 (draft)**.  A
single SER is emitted for every node that runs and contains:

* stable identifiers for the run, pipeline and node
* the node's upstream dependencies
* action information (operation reference and parameters)
* a minimal input/output delta
* check results explaining why the node ran and why it was considered OK
* timing information (wall and CPU)
* explicit status and optional error details
* optional summaries for input/output data and context snapshots

SERs are written to ``*.ser.jsonl`` files where each line is a JSON object.  Tools
and the Studio viewer consume these records directly.

Example::

   {
       "type": "ser",
       "schema_version": 2,
       "ids": {"run_id": "run-…", "pipeline_id": "plid-…", "node_id": "n-1"},
       "topology": {"upstream": []},
       "action": {
           "op_ref": "FloatMultiplyOperation",
           "params": {"factor": 2.0},
           "param_source": {"factor": "node"}
       },
       "io_delta": {"read": [], "created": [], "updated": [], "summaries": {}},
       "checks": {"why_run": {"trigger": "dependency", "upstream_evidence": [],
                   "pre": [], "policy": []},
                   "why_ok": {"post": [], "invariants": [],
                   "env": {}, "redaction": {}}},
       "timing": {"start": "…", "end": "…", "duration_ms": 12, "cpu_ms": 8},
       "status": "completed",
       "labels": {"node_fqn": "FloatMultiplyOperation"},
       "summaries": {
           "input_data": {"dtype": "FloatDataType", "sha256": "…"},
           "output_data": {"dtype": "FloatDataType", "sha256": "…"}
       }
   }

Detail flags control which summary fields are emitted when using the JSONL
driver:

* ``hash`` (default) – include ``sha256`` hashes only.
* ``repr`` – additionally include ``repr`` for input/output data.
* ``context`` – with ``repr`` also include ``repr`` for pre/post context.
* ``all`` – enable all of the above.

Versioning Policy
-----------------

.. note::
   **SER Versioning Policy:**
   
   * ``schema_version`` is a **major** integer for breaking changes only
   * v0 during pre-release development; v1 at first public release
   * Future breaking changes increment to v2, v3, etc.
   * Optional ``schema_tag`` field may be present but is not required by readers

Schema
------

The canonical JSON Schema ships with the package and can be loaded via:

.. code-block:: python

   from importlib import resources
   schema = resources.files("semantiva.trace.schema") / "ser_v0.schema.json"

IO Delta
--------
Each SER now includes an ``io_delta`` describing how the node interacted with context:

- ``read``: declared required keys (if provided by the processor)
- ``created``: new keys written by the node
- ``updated``: existing keys whose values changed
- ``summaries`` (changed keys only): ``dtype``, ``len``, ``rows``, and optional
  ``sha256`` (``hash`` flag) and ``repr`` (``repr`` flag)

Checks via SERHooks
-------------------
Orchestrator constructs basic hooks that fill:

- ``checks.why_run``: trigger and upstream evidence
- ``checks.why_ok``: post-check results, invariants (reserved), env pins, and redaction (reserved)

These are extension points for richer policy modules.

