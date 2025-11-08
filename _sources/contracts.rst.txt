Semantiva Contracts
===================

Semantiva components follow a set of metadata and type-contract rules.  The
:command:`semantiva dev lint` command audits components against these rules and
prints diagnostics with stable Semantiva Validation Assertions (``SVA``) codes.

Rule catalog
------------

.. include:: contracts_catalog.md
   :parser: myst_parser.sphinx_

Fixing common SVA errors
------------------------

- **SVA001-SVA003**: ensure all ``*_data_type`` methods are declared with
  ``@classmethod`` and use ``cls`` as the first argument.
- **SVA102**: keep component docstrings concise (under the configured
  character limit).
- **SVA104-SVA106**: ``injected_context_keys`` and
  ``suppressed_context_keys`` must be lists of unique strings without
  overlap.

Probe node contract (mandatory)
-------------------------------

- Any pipeline node wrapping a :class:`~semantiva.data_processors.data_processors.DataProbe`
  **must** declare a non-empty ``context_key``.
- The probe result is written to that key by the node—components stay
  context-agnostic.
- Pipelines that omit ``context_key`` for probes fail validation via
  :command:`semantiva inspect`.

CI integration
--------------

Use ``semantiva dev lint`` in CI pipelines to block merges when contracts are
violated. The command exits with code ``3`` (``EXIT_CONFIG_ERROR``) when any
``SVA`` error diagnostics are present; warnings do not affect the exit code.
