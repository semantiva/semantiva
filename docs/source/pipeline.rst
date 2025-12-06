Pipelines in Semantiva
======================

Pipelines orchestrate data operations, probes, sources, sinks and context
processors into a coherent execution graph.

This page has two parts:

- **Pipeline in Python** - for developers and advanced users: define, run and
  inspect pipelines directly in Python using
  :class:`semantiva.core.Payload` and :class:`semantiva.core.ContextType`
  while creating and testing components or exploring Semantiva.
- **Pipeline via CLI & YAML** - define the same ideas declaratively in YAML
  and run them from the command line. This is the **expected path for
  production pipelines**.

.. admonition:: Who this is for

   This page is the **pipeline user guide**. It assumes you have read
   :doc:`concepts`, :doc:`data_types`, :doc:`data_operations`,
   :doc:`data_probes`, :doc:`data_io` and :doc:`context_type`.

Pipeline in Python
------------------

In Python, developers and advanced users often work with pipeline
configurations directly as Python lists of nodes. This is especially useful
in notebooks and tests when:

- Creating and refining new processors.
- Learning how payload and context behave.
- Running ad-hoc or R&D workflows.

For long-lived, supported pipelines you are expected to use the declarative
YAML configuration described in :ref:`pipeline-via-yaml`.

Hello pipeline in pure Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with a minimal “hello” pipeline entirely in Python. The configuration is
a list of node definitions; each node references a processor **class** and its
parameters. The first node is a data source, so the incoming payload does not
need data.

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

   # [agent-fill-output: run the snippet above (using HELLO_PIPELINE_NODES)
   #  and paste the console output here]

In this example, the context remains empty for the entire execution. The
printed ``context`` shows the internal representation of
:class:`ContextType`, which should contain no keys after the pipeline runs.

Changing parameters via configuration vs context
------------------------------------------------

Semantiva resolves node parameters from configuration, context and Python
defaults, as described in :doc:`concepts`. A simple way to see this is to
reuse the pipeline configuration from the previous section and remove the
parameter from the node so that it is resolved from context instead.

Below we define a new configuration
``HELLO_PIPELINE_NODES_CONTEXT`` that is identical to
``HELLO_PIPELINE_NODES`` except that the :class:`FloatAddOperation` node has
no ``addend`` in its ``parameters`` mapping. The value is instead provided
via context under the same name.

.. code-block:: python

   from semantiva.core import ContextType, Payload
   from semantiva.pipeline import Pipeline
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

   # [agent-fill-output: run the snippet above with
   #  HELLO_PIPELINE_NODES_CONTEXT and paste the console output here]

Conceptually:

- In the **previous example** (``HELLO_PIPELINE_NODES``), the node's
  ``parameters`` mapping provides ``addend: 2.0``, so configuration supplies
  the value and the context stays empty.
- In **this example** (``HELLO_PIPELINE_NODES_CONTEXT``), ``addend`` is left
  undefined in the node and instead provided via
  ``context.set_value("addend", 2.0)``. The numerical result is the same,
  but the context now contains an entry for ``addend``.

Adding a probe node in Python
-----------------------------

Probes observe the data channel and return a value. The **pipeline node**, not
the probe component itself, decides whether to store that value in the context
via ``context_key``. Probe nodes must declare a non-empty ``context_key``.

To extend the Python pipeline with a probe, add a new node that wraps
:class:`FloatCollectValueProbe` and specifies a context key:

.. code-block:: python

   from semantiva.core import ContextType, Payload
   from semantiva.pipeline import Pipeline
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

   # [agent-fill-output: run the snippet above with
   #  PIPELINE_WITH_PROBE_NODES and paste the console output here]

From Python's perspective, you:

- Construct a :class:`Payload` with data and context (here data starts as
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

Pipeline via CLI and YAML
-------------------------
.. _pipeline-via-yaml:

Once you are comfortable with payloads and context, you can treat pipelines
as declarative configuration and run them from the CLI.

Start from the "hello" pipeline used in :doc:`getting_started`:

.. code-block:: yaml

   extensions: ["semantiva-examples"]

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: FloatAddOperation
         parameters:
           addend: 2.0

       - processor: FloatCollectValueProbe
         context_key: "result"
         
       - processor: template:"result_{result}.txt":path

       - processor: FloatTxtFileSaver

Save this as ``hello.yaml`` and run it:

.. code-block:: bash

   semantiva run hello.yaml

.. code-block:: console

   # [agent-fill-output: run `semantiva run hello.yaml` and paste the CLI output]

The fourth node writes into the context key ``result``, which is used to
define the output file path in the fifth node. The last node saves the final
float value to that file.

Extended inspection
-------------------

You can inspect a pipeline and its nodes without running it, or inspect a
specific run after execution.

.. code-block:: bash

   # Show pipeline structure and node types
   semantiva inspect hello.yaml

   # Show a specific run with extended inspection
   semantiva inspect hello.yaml --run last --extended

.. code-block:: console

   # [agent-fill-output: run the commands above and paste abbreviated outputs]

For full details on inspection, see :doc:`inspection` and :doc:`ser`.

