Run-Space Emission (Runtime)
============================

Semantiva emits dedicated lifecycle records when executing pipelines as part
of a run-space launch. The flow is fully deterministic and uses the
identifiers defined in the :doc:`trace schemas <trace_stream_v1>`.

Lifecycle
---------

1. **Compute identities**
   - ``run_space_spec_id`` — canonical hash of the run-space configuration
   - ``run_space_inputs_id`` *(optional)* — hash of referenced inputs when
     fingerprints are present
   - ``run_space_input_fingerprints`` — file fingerprint entries emitted only on
     ``run_space_start``
2. **Create launch/session**
   - ``run_space_launch_id`` — provided via CLI, derived from an idempotency key,
     or generated as a UUIDv7 fallback
   - ``run_space_attempt`` — integer retry counter (1-based)
3. **Emit ``run_space_start``** with the identifiers above and the planned run count
4. **Execute pipelines** — each ``pipeline_start`` record is linked back to the
   enclosing run-space via foreign keys
5. **Emit ``run_space_end``** summarising the launch outcome

Pipeline linkage
----------------

``pipeline_start`` records include the run-space identifiers when a run-space
context is active. Standalone pipelines (without a run-space) omit these
fields entirely for backwards compatibility.

Standalone runs
----------------

When pipelines are executed outside of a run-space, the runtime skips the
lifecycle records and the foreign keys, preserving existing behaviour.
