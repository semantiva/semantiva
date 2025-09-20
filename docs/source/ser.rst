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

Example SER
-----------

.. code-block:: json

   {
     "type": "ser",
     "schema_version": 0,
     "ids": {"run_id": "run-…", "pipeline_id": "plid-…", "node_id": "n-3"},
     "topology": {"upstream": ["n-2"]},
     "action": {
       "op_ref": "FloatBasicProbe",
       "params": {"context_keyword": "probed_data"},
       "param_source": {"context_keyword": "node"}
     },
     "io_delta": {
       "read": ["probed_data"],
       "created": ["probed_data"],
       "updated": [],
       "summaries": {
         "probed_data": {"dtype": "FloatDataType", "len": 1}
       }
     },
     "checks": {
       "why_run": {
         "trigger": "dependency",
         "upstream_evidence": [{"node_id": "n-2", "state": "completed"}],
         "pre": [
           {
             "code": "required_keys_present",
             "result": "PASS",
             "details": {"expected": ["probed_data"], "missing": []}
           },
           {
             "code": "input_type_ok",
             "result": "PASS",
             "details": {"expected": "FloatDataType", "actual": "FloatDataType"}
           }
         ],
         "policy": []
       },
       "why_ok": {
         "post": [
           {
             "code": "output_type_ok",
             "result": "PASS",
             "details": {"expected": "FloatDataType", "actual": "FloatDataType"}
           },
           {
             "code": "context_writes_realized",
             "result": "PASS",
             "details": {"created": ["probed_data"], "updated": [], "missing": []}
           }
         ],
         "invariants": [],
         "env": {
           "python": "3.11.2",
           "implementation": "cpython",
           "platform": "Linux-…",
           "semantiva": "0.1.0.dev0+dummy",
           "numpy": null,
           "pandas": null
         },
         "redaction": {}
       }
     },
     "timing": {"start": "…", "end": "…", "duration_ms": 5, "cpu_ms": 4},
     "status": "completed",
     "labels": {"node_fqn": "FloatBasicProbe"},
     "summaries": {
       "input_data": {"dtype": "FloatDataType", "sha256": "…"},
       "output_data": {"dtype": "FloatDataType", "sha256": "…"}
     }
   }

The ``checks`` block now always contains:

* ``why_run.pre`` – built-in validation executed before the node runs.
* ``why_ok.post`` – output validations that ran after the node returned.
* ``why_ok.env`` – minimal, non-sensitive environment pins for reproducibility.

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
The template-method orchestrator collects SER evidence centrally. The base
:py:class:`~semantiva.execution.orchestrator.orchestrator.SemantivaOrchestrator`
builds the pre/post check lists, captures ``io_delta`` snapshots, and pins the
runtime environment exactly once per node. Downstream policy engines can extend
these hooks (for example via ``_extra_pre_checks``) but every SER produced
by the runtime includes the following checks out of the box—even on error.
When a node fails, the exception entry is followed by the standard
``output_type_ok`` and ``context_writes_realized`` checks so failure records
retain the same structure as successful ones.

Built-in checks
---------------

The runtime emits the following check entries for every node:

.. list-table::
   :header-rows: 1

   * - Code
     - Channel
     - Purpose
     - PASS
     - WARN / FAIL
   * - ``required_keys_present``
     - ``why_run.pre``
     - Declared context keys are available before execution.
     - All required keys present.
     - Missing keys listed in ``details.missing``.
   * - ``input_type_ok``
     - ``why_run.pre``
     - Input payload matches the processor's ``input_data_type``.
     - ``details.actual`` matches ``details.expected``.
     - Type mismatch triggers ``FAIL``.
   * - ``config_valid``
     - ``why_run.pre``
     - Node configuration contains no unrecognised parameters.
     - ``WARN`` lists ``details.invalid``; omitted when the node cannot report invalid parameters.
     - ``WARN`` when inspection detected invalid parameters.
   * - ``output_type_ok``
     - ``why_ok.post``
     - Output payload matches the processor's ``output_data_type``.
     - ``details.actual`` matches ``details.expected``.
     - Type mismatch triggers ``FAIL``.
   * - ``context_writes_realized``
     - ``why_ok.post``
     - Context keys declared in ``io_delta.created``/``updated`` exist after execution.
     - All declared keys materialised, ``details.missing`` empty.
     - ``FAIL`` when writes were declared but no value was persisted.

Environment pins
----------------

``checks.why_ok.env`` captures a reproducibility snapshot: Python runtime,
implementation, platform string, Semantiva version, and optional third-party
versions (``numpy``/``pandas`` when installed). Values are simple strings or
``null`` and contain no host-specific secrets.

