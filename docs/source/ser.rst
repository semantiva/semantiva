Step Evidence Record (SER)
==========================

Semantiva records pipeline execution using the **Step Evidence Record (SER)**.  A
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
       "action": {"op_ref": "MyOp", "params": {}, "param_source": {}},
       "io_delta": {"read": [], "created": [], "updated": [], "summaries": {}},
       "checks": {"why_run": {"trigger": "dependency", "upstream_evidence": [],
                   "pre": [], "policy": []},
                   "why_ok": {"post": [], "invariants": [],
                   "env": {}, "redaction": {}}},
       "timing": {"start": "…", "end": "…", "duration_ms": 12, "cpu_ms": 8},
       "status": "completed",
       "summaries": {
           "input_data": {"sha256": "…"},
           "output_data": {"sha256": "…"},
           "pre_context": {"sha256": "…"},
           "post_context": {"sha256": "…"}
       }
   }

Detail flags control which summary fields are emitted when using the JSONL
driver:

* ``hash`` (default) – include ``sha256`` hashes only.
* ``repr`` – additionally include ``repr`` for input/output data.
* ``context`` – with ``repr`` also include ``repr`` for pre/post context.
* ``all`` – enable all of the above.

Legacy trace files can be converted to SER using the ``semantiva trace convert``
command.

