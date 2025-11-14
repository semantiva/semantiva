Creating Components (Authoring Guide)
=====================================
Audience
--------
Developers adding domain behavior via **operations**, **probes**, **sources/sinks**, or **context processors**.

Do This / Not That
-------------------

- ✅ Use **DataOperation** for transformations (may update context).
- ✅ Use **DataProbe** for read-only analysis:
  - Declare **only** ``input_data_type``.
  - **Do not** declare ``output_data_type``.
  - **Do not** declare or mutate context keys (probes are read-only).
- ✅ Use **DataSource** / **DataSink** for I/O; **ContextProcessor** for domain context logic.
- ❌ Do *not* subclass internal/private processor bases.
- ✅ Keep constructors minimal (base classes already wire logging/observer).

Contract Highlights
--------------------
``input_data_type`` / ``output_data_type`` are **@classmethod** and return **types** (not instances) where applicable.

- **DataProbe**:
  - must declare ``input_data_type``,
  - **must not** declare ``output_data_type``,
  - **must not** create/update context.
- **DataSink** must **not** declare an output type.

Minimal Templates (pass lint)
-----------------------------

DataOperation (transforms; may update context)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.data_processors import DataOperation
    from semantiva.examples.test_utils import FloatDataType

    class DemoNormalize(DataOperation):
        """Normalize floats; writes mean/std to context."""

        @classmethod
        def input_data_type(cls):
            return FloatDataType

        @classmethod
        def output_data_type(cls):
            return FloatDataType

        @classmethod
        def get_created_keys(cls) -> set[str]:
            """Context keys this processor may create."""
            return {"norm.mean", "norm.std"}

        def _process_logic(self, data: FloatDataType, *, epsilon: float = 1e-8):
            # Example context write via observer hook
            self._notify_context_update("norm.mean", 0.0)
            self._notify_context_update("norm.std", 1.0)
            return data



In real components you must **register** any context keys you create. The
``get_created_keys`` class method is used by the inspection and context observer
machinery to validate updates and to expose them in tools such as
``semantiva inspect`` and ``semantiva dev lint``.
DataProbe (read-only; no context creation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.data_processors import DataProbe
    from semantiva.examples.test_utils import FloatDataType

    class DemoProbeReadOnly(DataProbe):
        """Probe floats (read-only); does not mutate context."""

        @classmethod
        def input_data_type(cls):
            return FloatDataType

        def _process_logic(self, data: FloatDataType, *, threshold: float = 3.0):
            # Analysis only; DO NOT update context
            return data

.. note::

   Probe components never write to context themselves. When the pipeline node
   specifies ``context_key``, the node stores the probe result in context after
   ``process`` returns, keeping the component stateless.

DataSource (produces data; declares only output type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.data_io import DataSource
    from semantiva.examples.test_utils import FloatDataType

    class DemoSource(DataSource):
        """Emit floats from a backing store."""

        @classmethod
        def output_data_type(cls):
            return FloatDataType

        @classmethod
        def _get_data(cls, count: int = 3):
            return [1.0, 2.0, 3.0][:count]

DataSink (consumes data; declares only input type)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from semantiva.data_io import DataSink
    from semantiva.examples.test_utils import FloatDataType

    class DemoSink(DataSink[FloatDataType]):
        """Persist floats to a sink."""

        @classmethod
        def input_data_type(cls):
            return FloatDataType

        @classmethod
        def _send_data(cls, data: FloatDataType, *, path: str = "out.txt"):
            return None

Context Processors (domain context logic)
-----------------------------------------
Use a context processor for creating/merging domain context. Keep them focused on
context state, not data transformations. Run the linter to verify contracts.

Linting Your Components
-----------------------

Run contract checks with the CLI:

.. code-block:: bash

    # Validate modules
    semantiva dev lint --modules my_package.ext

    # Scan source paths
    semantiva dev lint --paths ./src ./plugins

    # Validate components referenced by YAML
    semantiva dev lint --yaml pipeline.yaml

    # Export the rule catalog
    semantiva dev lint --export-contracts CONTRACTS.md

    # Detailed diagnostics
    semantiva dev lint --modules my_package.ext --debug

