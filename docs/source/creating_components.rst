Creating Components (Authoring Guide)
=====================================
Audience
--------
Developers adding domain behavior via **operations**, **probes**, **sources/sinks**, or **context processors**.

.. admonition:: Who this is for

   This page is for **framework developers and component authors**.
   It assumes you are comfortable running and tweaking pipelines as
   described in :doc:`personas/pipeline_users` and that you can read
   basic Python code.

   If you only need to run existing pipelines, stay with :doc:`pipelines_yaml`
   and :doc:`personas/pipeline_users`.

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
        def get_created_keys(cls) -> list[str]:
            """Context keys this processor may create."""
            return ["norm.mean", "norm.std"]

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

.. admonition:: Do not pass ContextType into processors

   Components must never accept ``ContextType`` directly in their ``process``
   or ``_process_logic`` methods. Context access is always mediated by pipeline
   nodes and observers.

.. code-block:: python

   # ❌ Anti-pattern: do NOT copy this

   from semantiva.context_processors.context_types import ContextType

   class BadProbe:
       @classmethod
       def input_data_type(cls):
           return FloatDataType

       def _process_logic(self, data, context: ContextType):  # <-- wrong
           context.set_value("some.key", 1.23)
           return data

Use a ``DataProbe`` that returns values, and let the node write them into
context using a ``context_key`` as shown in :ref:`probe-nodes`.

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
context state, not data transformations.

Linting Your Components
-----------------------

Use the :command:`semantiva dev lint` CLI to run static contract checks against
your components. It can discover processors from Python modules, source paths,
Semantiva extensions, or pipeline YAML files.

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

When linting flags SVA codes, consult :doc:`contracts` and follow the
:ref:`sva-troubleshooting-workflow` to fix issues before shipping.


Minimal dev loop: component in a Python pipeline
------------------------------------------------

As a component author, you will often want to **declare a component,
plug it into a pipeline, run it once, and inspect the result**.

The example below assumes you have a simple operation already defined
(similar to the ``FloatAddOperation`` used in other examples).

.. code-block:: python

   from semantiva import ContextType, Payload, Pipeline
   from semantiva.data_types import BaseDataType
   from semantiva.data_processors import DataOperation

   class FloatDataType(BaseDataType[float]):
       def validate(self, data: float) -> bool:
           return True

   class DemoAdd(DataOperation):
       """Toy example: add a constant to a float."""

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType

       def _process_logic(self, data: FloatDataType) -> FloatDataType:
           # For demonstration purposes, we just add 1.0
           return FloatDataType(data.data + 1.0)

   # A minimal Python pipeline that uses DemoAdd
   HELLO_PIPELINE_NODES = [
       {
           "processor": DemoAdd,
           "parameters": {},
       },
   ]

   pipeline = Pipeline(HELLO_PIPELINE_NODES)
   context = ContextType()
   payload = Payload(data=FloatDataType(41.0), context=context)
   result_payload = pipeline.process(payload)

   print("Result data:", result_payload.data)
   print("Context:", result_payload.context)

.. code-block:: console

   2025-12-06 19:51:34,769 - INFO     - Starting pipeline with 1 nodes (pipeline)
   2025-12-06 19:51:34,770 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 19:51:34,770 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.001274s; Elapsed CPU Time: 0.001270s
                   Node 1: DemoAdd;        Elapsed CPU Time: 0.000069s;    Elapsed Wall Time: 0.000071s
    (pipeline)
   Result data: FloatDataType(42.0)
   Context: ContextType(context={})

This pattern is a **development feedback loop**: declare a component,
wire it into a Python pipeline, run it once, and inspect the
behaviour.

For **production use**, the same component would typically be
referenced from a **YAML pipeline configuration** instead
(see :doc:`pipelines_yaml` and :doc:`contracts` for details).
