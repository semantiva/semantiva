Semantic Execution Record (SER) v1
==================================

Semantiva records pipeline execution using the **Semantic Execution Record (SER) v1**.  A
single SER is emitted for every node that runs and contains:

* stable identifiers for the run, pipeline and node under ``identity``
* the node's upstream dependencies via ``dependencies.upstream``
* processor details (``processor.ref`` with parameters and their sources)
* a minimal context delta describing reads and writes
* structured assertions explaining why the node ran and why it was OK
* timing information (wall and CPU)
* explicit status and optional error details
* optional summaries for input/output data and context snapshots
* optional ``tags`` for downstream correlation

SERs are written to ``*.ser.jsonl`` files where each line is a JSON object.  Tools
and the Studio viewer consume these records directly.

Example SER
-----------

.. code-block:: json

   {
     "record_type": "ser",
     "schema_version": 1,
     "identity": {"run_id": "run-…", "pipeline_id": "plid-…", "node_id": "n-3"},
     "dependencies": {"upstream": ["n-2"]},
     "processor": {
       "ref": "semantiva.examples.test_utils.FloatBasicProbe",
       "parameters": {"context_key": "probed_data"},
       "parameter_sources": {"context_key": "node"}
     },
     "context_delta": {
       "read_keys": ["probed_data"],
       "created_keys": ["probed_data"],
       "updated_keys": [],
       "key_summaries": {
         "probed_data": {"dtype": "FloatDataType", "len": 1}
       }
     },
     "assertions": {
       "trigger": "dependency",
       "upstream_evidence": [{"node_id": "n-2", "state": "succeeded"}],
       "preconditions": [
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
       "postconditions": [
         {
           "code": "output_type_ok",
           "result": "PASS",
           "details": {"expected": "FloatDataType", "actual": "FloatDataType"}
         },
         {
           "code": "context_writes_realized",
           "result": "PASS",
           "details": {"created_keys": ["probed_data"], "updated_keys": [], "missing_keys": []}
         }
       ],
       "invariants": [],
       "environment": {
         "python": "3.12.0",
         "platform": "Linux-…",
         "semantiva": "0.2.0.dev0",
         "numpy": null,
         "pandas": null
       },
       "redaction_policy": {},
       "args": {"run_space.index": 1, "run_space.combine": "product"}
     },
     "timing": {"started_at": "…", "finished_at": "…", "duration_ms": 5, "cpu_ms": 4},
     "status": "succeeded",
     "tags": {"node_ref": "semantiva.examples.test_utils.FloatBasicProbe"},
     "summaries": {
       "input_data": {"dtype": "FloatDataType", "sha256": "…"},
       "output_data": {"dtype": "FloatDataType", "sha256": "…"}
     }
   }

The ``assertions`` block always contains structured evidence describing why the
node ran and why it was considered successful. Additional metadata (like
``trigger`` and ``upstream_evidence``) is included alongside the formal
preconditions/postconditions for convenient consumption.

Detail flags control which summary fields are emitted when using the JSONL
driver:

* ``hash`` (default) - include ``sha256`` hashes only.
* ``repr`` - additionally include ``repr`` for input/output data.
* ``context`` - with ``repr`` also include ``repr`` for pre/post context.
* ``all`` - enable all of the above.

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
   schema = resources.files("semantiva.trace.schema") / "semantic_execution_record_v1.schema.json"

Context Delta
-------------
Each SER includes a ``context_delta`` describing how the node interacted with context:

- ``read_keys``: declared required keys (if provided by the processor)
- ``created_keys``: new keys written by the node
- ``updated_keys``: existing keys whose values changed
- ``key_summaries`` (changed keys only): ``dtype``, ``len``, ``rows``, and optional
  ``sha256`` (``hash`` flag) and ``repr`` (``repr`` flag)

Assertions via SERHooks
-----------------------
The template-method orchestrator collects SER evidence centrally. The base
:py:class:`~semantiva.execution.orchestrator.orchestrator.SemantivaOrchestrator`
builds the pre/post assertion lists, captures ``context_delta`` snapshots, and pins the
runtime environment exactly once per node. Downstream policy engines can extend
these hooks (for example via ``_extra_pre_checks``) but every SER produced
by the runtime includes the following assertions out of the box—even on error.
When a node fails, the exception entry is followed by the standard
``output_type_ok`` and ``context_writes_realized`` checks so failure records
retain the same structure as successful ones.

Built-in assertions
-------------------

The runtime emits the following assertion entries for every node:

.. list-table::
   :header-rows: 1

   * - Code
     - Channel
     - Purpose
     - PASS
     - WARN / FAIL
   * - ``required_keys_present``
     - ``assertions.preconditions``
     - Declared context keys are available before execution.
     - All required keys present.
     - Missing keys listed in ``details.missing``.
   * - ``input_type_ok``
     - ``assertions.preconditions``
     - Input payload matches the processor's ``input_data_type``.
     - ``details.actual`` matches ``details.expected``.
     - Type mismatch triggers ``FAIL``.
   * - ``config_valid``
     - ``assertions.preconditions``
     - Node configuration contains no unrecognised parameters.
     - ``WARN`` lists ``details.invalid``; omitted when the node cannot report invalid parameters.
     - ``WARN`` when inspection detected invalid parameters.
   * - ``output_type_ok``
     - ``assertions.postconditions``
     - Output payload matches the processor's ``output_data_type``.
     - ``details.actual`` matches ``details.expected``.
     - Type mismatch triggers ``FAIL``.
   * - ``context_writes_realized``
     - ``assertions.postconditions``
     - Context keys declared in ``context_delta.created_keys``/``updated_keys`` exist after execution.
     - All declared keys materialised, ``details.missing_keys`` empty.
     - ``FAIL`` when writes were declared but no value was persisted.

Environment pins
----------------

``assertions.environment`` captures a reproducibility snapshot: Python runtime,
implementation, platform string, Semantiva version, and optional third-party
versions (``numpy``/``pandas`` when installed). Values are simple strings or
``null`` and contain no host-specific secrets.
