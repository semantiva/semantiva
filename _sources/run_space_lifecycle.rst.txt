Run-Space Lifecycle
===================

Semantiva traces Run-Spaces as a lifecycle enclosing one or many pipeline runs.

Records
-------

- ``run_space_start`` — emitted once per launch/session
- ``run_space_end`` — emitted after the launch completes

Identity Model
--------------

**Plan identity** — ``run_space_spec_id``  
Run-Space Configuration Format (**RSCF v1**): canonicalize the run-space specification (sort object keys; preserve array order;
canonical scalars; normalize ``\n``; YAML anchors/comments removed at parse; serialize to
compact UTF-8 JSON). Hash preimage is namespaced:

.. code-block:: text

   run_space_spec_id = sha256( b"semantiva:rscf1:" + <canonical_spec_bytes> ).hexdigest()

**Inputs snapshot** — ``run_space_inputs_id`` (optional)  
Run-Space Materialization (**RSM v1**): canonicalize the set of input fingerprints (sort by role,uri; each carries digest.sha256);
then:

.. code-block:: text

   run_space_inputs_id = sha256( b"semantiva:rsm1:" + run_space_spec_id + ":" + <canonical_fps_bytes> ).hexdigest()

Omit ``run_space_inputs_id`` when the run-space is self-contained (no external inputs).

**Launch/session** — ``run_space_launch_id``  
Unique id for this launch (e.g., UUIDv7 or sha256(materialization + idempotency_key)).

**Attempt** — ``run_space_attempt``  
1-based retry counter within the same launch id.

Planned Runs
------------

``run_space_planned_run_count`` declares the planned number of pipeline runs for this launch.

Linkage to Pipelines
--------------------

Each pipeline spawned from the launch includes a **composite foreign key** in its
``pipeline_start`` record to uniquely identify the launch:

- ``run_space_launch_id`` + ``run_space_attempt`` — composite FK (both parts needed for retry disambiguation)

Plus run-specific metadata:

- ``run_space_index`` — 0-based position within the launch
- ``run_space_context`` — parameter values for this specific run

Launch-level constants (``run_space_spec_id``, ``run_space_inputs_id``, ``run_space_combine_mode``, 
``run_space_total_runs``) are stored once in the ``run_space_start`` event to eliminate redundancy.
Standalone pipelines omit all run-space fields.
