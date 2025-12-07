.. _pipelines_python:

Pipelines in Python
===================

.. admonition:: Who this is for

   This page is for **framework developers, component authors and
   advanced R&D workflows**.
   You define and run pipelines directly in Python for rapid iteration,
   testing, and learning Semantiva.

   For **production pipelines** and configuration as an artefact of
   record, see :doc:`pipelines_yaml` instead.

Overview
--------

Python pipelines let you exercise the same execution engine used for
YAML pipelines, but without creating a production configuration artefact.
Use them for notebooks, tests, and quick feedback loops while developing
processors. Once stable, port the configuration to YAML for CLI use and
version control.

Hello pipeline in pure Python
-----------------------------

Start with a minimal “hello” pipeline entirely in Python. The
configuration is a list of node definitions; each node references a
processor **class** and its parameters. The first node is a data source,
so the incoming payload does not need data.

.. code-block:: python

   from semantiva import ContextType, Payload, Pipeline

   # Example processors used in this guide
   from semantiva.examples.test_utils import (
       FloatValueDataSource,
       FloatAddOperation,
   )

   # Python configuration for a simple arithmetic pipeline.
   HELLO_PIPELINE_NODES = [
       {
           "processor": FloatValueDataSource,
           "parameters": {
               "value": 1.0,   # fixed in configuration
           },
       },
       {
           "processor": FloatAddOperation,
           "parameters": {
               "addend": 2.0,  # fixed in configuration
           },
       },
   ]

   # Build the pipeline directly from the Python configuration above.
   pipeline = Pipeline(HELLO_PIPELINE_NODES)

   # Create payload and context explicitly. Payload starts with no data because
   # the first node is a data source.
   context = ContextType()
   payload = Payload(data=None, context=context)

   # Run the pipeline.
   result_payload = pipeline.process(payload)

   print("data:", result_payload.data.data)
   print("context:", result_payload.context)

.. code-block:: console

   2025-12-06 15:35:26,375 - INFO     - Starting pipeline with 2 nodes (pipeline)
   2025-12-06 15:35:26,377 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 15:35:26,377 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.001885s; Elapsed CPU Time: 0.001882s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000059s;    Elapsed Wall Time: 0.000061s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000069s;    Elapsed Wall Time: 0.000071s
    (pipeline)
   data: 3.0
   context: ContextType(context={})

In this example, the context remains empty for the entire execution. The
printed ``context`` shows the internal representation of ``ContextType``,
which should contain no keys after the pipeline runs.

Changing parameters via configuration vs context
------------------------------------------------

Semantiva resolves node parameters from configuration, context and Python
defaults, as described in :doc:`concepts`. A simple way to see this is to
reuse the pipeline configuration from the previous section and remove the
parameter from the node so that it is resolved from context instead.

Below we define a new configuration
``HELLO_PIPELINE_NODES_CONTEXT`` that is identical to
``HELLO_PIPELINE_NODES`` except that the ``FloatAddOperation`` node has
no ``addend`` in its ``parameters`` mapping. The value is instead provided
via context under the same name.

.. code-block:: python

   from semantiva import ContextType, Payload, Pipeline
   from semantiva.examples.test_utils import (
       FloatValueDataSource,
       FloatAddOperation,
   )

   # Same structure as HELLO_PIPELINE_NODES, but without "addend" in the
   # parameters mapping for FloatAddOperation.
   HELLO_PIPELINE_NODES_CONTEXT = [
       {
           "processor": FloatValueDataSource,
           "parameters": {
               "value": 1.0,
           },
       },
       {
           "processor": FloatAddOperation,
           # No 'addend' here: it will be resolved from the context.
           "parameters": {},
       },
   ]

   pipeline = Pipeline(HELLO_PIPELINE_NODES_CONTEXT)

   # Context now provides the value for "addend".
   context = ContextType()
   context.set_value("addend", 2.0)

   # As before, data is None because the first node is a data source.
   payload = Payload(data=None, context=context)
   result_payload = pipeline.process(payload)

   print("data:", result_payload.data.data)
   print("context:", result_payload.context)

.. code-block:: console

   2025-12-06 15:35:39,113 - INFO     - Starting pipeline with 2 nodes (pipeline)
   2025-12-06 15:35:39,115 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 15:35:39,115 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.001887s; Elapsed CPU Time: 0.001884s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000073s;    Elapsed Wall Time: 0.000073s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000046s;    Elapsed Wall Time: 0.000046s
    (pipeline)
   data: 3.0
   context: ContextType(context={'addend': 2.0})

Conceptually:

- In the **previous example** (``HELLO_PIPELINE_NODES``), the node's
  ``parameters`` mapping provides ``addend: 2.0``, so configuration supplies
  the value and the context stays empty.
- In **this example** (``HELLO_PIPELINE_NODES_CONTEXT``), ``addend`` is left
  undefined in the node and instead provided via
  ``context.set_value("addend", 2.0)``. The numerical result is the same,
  but the context now contains an entry for ``addend``.

.. _probe-nodes:

Adding a probe node in Python
-----------------------------

Probes observe the data channel and return a value. The **pipeline node**, not
the probe component itself, decides whether to store that value in the context
via ``context_key``. Probe nodes must declare a non-empty ``context_key`` to
satisfy :doc:`contracts`.

To extend the Python pipeline with a probe, add a new node that wraps
``FloatCollectValueProbe`` and specifies a context key:

.. code-block:: python

   from semantiva import ContextType, Payload, Pipeline
   from semantiva.examples.test_utils import (
       FloatValueDataSource,
       FloatAddOperation,
       FloatCollectValueProbe,
   )

   # Configuration with a probe node at the end.
   PIPELINE_WITH_PROBE_NODES = [
       {
           "processor": FloatValueDataSource,
           "parameters": {
               "value": 1.0,
           },
       },
       {
           "processor": FloatAddOperation,
           "parameters": {
               "addend": 2.0,
           },
       },
       {
           # Probe node: observes data and writes result into context["result"].
           "processor": FloatCollectValueProbe,
           "context_key": "result",   # mandatory for probe nodes
           "parameters": {},
       },
   ]

   pipeline = Pipeline(PIPELINE_WITH_PROBE_NODES)

   context = ContextType()
   payload = Payload(data=None, context=context)

   result_payload = pipeline.process(payload)

   print("data:", result_payload.data.data)
   print("context:", result_payload.context)
   print("result in context:", result_payload.context.get_value("result"))

.. code-block:: console

   2025-12-06 15:35:45,248 - INFO     - Starting pipeline with 3 nodes (pipeline)
   2025-12-06 15:35:45,251 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 15:35:45,251 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.002366s; Elapsed CPU Time: 0.002362s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000104s;    Elapsed Wall Time: 0.000105s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000060s;    Elapsed Wall Time: 0.000060s
                   Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000059s;    Elapsed Wall Time: 0.000059s
    (pipeline)
   data: 3.0
   context: ContextType(context={'result': 3.0})
   result in context: 3.0

From Python's perspective, you:

- Construct a ``Payload`` with data and context (here data starts as
  ``None`` because the first node is a data source).
- Call ``pipeline.process``.
- Let the last node add the ``"result"`` entry to the context.

In notebooks or test modules, you will often:

- Define processors (see :doc:`creating_components`) and small pipeline
  configurations such as ``HELLO_PIPELINE_NODES`` or
  ``PIPELINE_WITH_PROBE_NODES`` side by side.
- Run them with different payloads and contexts to debug behaviour.
- Once stable, port the configuration to YAML for CLI use and version
  control.

Where to go next
----------------

- To see how the same concepts are expressed in YAML for production
  use, see :doc:`pipelines_yaml`.
- If you author components, also visit :doc:`creating_components`
  and :doc:`contracts`.
