Pipelines in Semantiva
======================

Pipelines orchestrate data operations, probes, sources, sinks and context
processors into a coherent execution graph.

This page has two parts:

- **Pipeline in Python** - for developers and advanced users: define, run and
  inspect pipelines directly in Python using
  ``Payload`` and ``ContextType`` while creating and testing components or
  exploring Semantiva.
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
YAML configuration described later in this guide.

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
via ``context_key``. Probe nodes must declare a non-empty ``context_key``.

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

   2025-12-06 15:36:04,361 - INFO     - ▶️  Run 1/1 starting (__init__)
   2025-12-06 15:36:04,361 - INFO     - Starting pipeline with 5 nodes (pipeline)
   2025-12-06 15:36:04,366 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 15:36:04,366 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.004282s; Elapsed CPU Time: 0.004281s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000110s;    Elapsed Wall Time: 0.000111s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000065s;    Elapsed Wall Time: 0.000066s
                   Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000057s;    Elapsed Wall Time: 0.000057s
                   Node 4: Template_path;  Elapsed CPU Time: 0.000053s;    Elapsed Wall Time: 0.000053s
                   Node 5: FloatTxtFileSaver;      Elapsed CPU Time: 0.000156s;    Elapsed Wall Time: 0.000156s
    (pipeline)
   2025-12-06 15:36:04,366 - INFO     - ✅ Run 1/1 completed in 0.00s (__init__)
   2025-12-06 15:36:04,366 - INFO     - Output data: FloatDataType(3.0) (__init__)
   2025-12-06 15:36:04,366 - INFO     - Output context:
     result: 3.0
     path: 'result_3.0.txt' (__init__)

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

   Configuration Identity
   - Semantic ID: plsemid-f5763497bd3f198e46e72f22b92a2eda7a14fa336374d795e7f37ea31c1b7447
   - Config ID:   plcid-25b95b9f40912aabde25e36ac913e2665da935cdc68775020b2f9b1c72a94724
   - Run-Space Config ID: none
   Required Context Keys: none

   Pipeline Structure:
           Required context keys: None

           1. Node: FloatValueDataSource (DataSource)
                   Parameters: value
                           From pipeline configuration: value=1.0
                           From processor defaults: None
                           From context: None
                   Context additions: None
                   Invalid parameters:
                   Configuration valid: True

           2. Node: FloatAddOperation (DataOperation)
                   Parameters: addend
                           From pipeline configuration: addend=2.0
                           From processor defaults: None
                           From context: None
                   Context additions: None
                   Invalid parameters:
                   Configuration valid: True

           3. Node: FloatCollectValueProbe (DataProbe)
                   Parameters: None
                           From pipeline configuration: None
                           From processor defaults: None
                           From context: None
                   Context additions: result
                   Invalid parameters:
                   Configuration valid: True

           4. Node: Template_path (ContextProcessor)
                   Parameters: result
                           From pipeline configuration: None
                           From processor defaults: None
                           From context: result (from Node 3)
                   Context additions: path
                   Invalid parameters:
                   Configuration valid: True

           5. Node: FloatTxtFileSaver (DataSink)
                   Parameters: path
                           From pipeline configuration: None
                           From processor defaults: None
                           From context: path (from Node 4)
                   Context additions: None
                   Invalid parameters:
                   Configuration valid: True

   ----------------------------------------

   Extended Pipeline Inspection:
           Required context keys: None

   Node 1: FloatValueDataSource (FloatValueDataSource_DataSourceNode)
       - UUID: 66732bf0-1c9f-5d36-9edc-250025dbc34e
       - Role: DataSource
       - FQCN: semantiva.examples.test_utils.FloatValueDataSource
       - Node Semantic ID: none
       - Component type: DataSource
       - Input data type: NoDataType
       - Output data type: FloatDataType
       - Parameters from pipeline configuration: value=1.0
       - Parameters from processor defaults: None
       - Parameters from context: None
       - Context additions: None
       - Context suppressions: None
       - Invalid parameters:
       - Configuration valid: True

   ... (nodes 2-5 follow, matching the summary above, including context additions for the template and sink)

For full details on inspection, see :doc:`inspection` and :doc:`ser`.

