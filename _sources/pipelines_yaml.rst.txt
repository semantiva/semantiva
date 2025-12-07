.. _pipelines_yaml:

Pipelines - YAML & CLI
======================

.. admonition:: Who this is for

   This page is for **pipeline users and operators**.
   You primarily work with **YAML pipeline configurations** and the
   :command:`semantiva` CLI, not with the Python internals.

   If you are developing new components or exploring Semantiva in
   notebooks, see :doc:`pipelines_python` instead.

Overview
--------

Production pipelines are **declared in YAML** and executed with the
:command:`semantiva` CLI. YAML files are the **configuration artefact of
record**: they are versioned, validated, inspected and promoted across
environments.

Each pipeline YAML describes a graph of nodes under ``pipeline:`` ->
``nodes:``. Nodes wrap processors (sources, operations, probes,
context processors, sinks) and keep the **data** and **context**
channels separate for traceability. Probes remain read-only and write
results into context via the node's ``context_key``.

Running a YAML pipeline
-----------------------

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

The probe node writes into the context key ``result``, which is used to
define the output file path in the following context processor. The last
node saves the final float value to that file. This YAML probe example is
used as the canonical reference for probe behaviour in
:doc:`contracts`.

Validation & inspection from YAML
---------------------------------

Treat YAML files as governed artefacts: inspect their structure and identities
before or after execution.

.. code-block:: bash

   # Show pipeline structure and node types
   semantiva inspect hello.yaml

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

.. code-block:: bash

   # Show extended pipeline inspection
   semantiva inspect hello.yaml --extended

.. code-block:: console

   Configuration Identity
   - Semantic ID: plsemid-f5763497bd3f198e46e72f22b92a2eda7a14fa336374d795e7f37ea31c1b7447
   - Config ID:   plcid-25b95b9f40912aabde25e36ac913e2665da935cdc68775020b2f9b1c72a94724
   - Run-Space Config ID: none
   Required Context Keys: none

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

   Node 2: FloatAddOperation (FloatAddOperation_DataOperationNode)
       - UUID: 7050e834-fa1d-58ae-86eb-c99af6d843ba
       - Role: DataOperation
       - FQCN: semantiva.examples.test_utils.FloatAddOperation
       - Node Semantic ID: none
       - Component type: DataOperation
       - Input data type: FloatDataType
       - Output data type: FloatDataType
       - Parameters from pipeline configuration: addend=2.0
       - Parameters from processor defaults: None
       - Parameters from context: None
       - Context additions: None
       - Context suppressions: None
       - Invalid parameters:
       - Configuration valid: True

   Node 3: FloatCollectValueProbe (FloatCollectValueProbe_ProbeContextInjectorNode)
       - UUID: fba10857-e90a-5370-9126-5911e4bd5aac
       - Role: DataProbe
       - FQCN: semantiva.examples.test_utils.FloatCollectValueProbe
       - Node Semantic ID: none
       - Component type: DataProbe
       - Input data type: FloatDataType
       - Output data type: FloatDataType
       - Parameters from pipeline configuration: None
       - Parameters from processor defaults: None
       - Parameters from context: None
       - Context additions: result
       - Context suppressions: None
       - Invalid parameters:
       - Configuration valid: True

   Node 4: Template_path (Template_path_ContextProcessorNode)
       - UUID: 90254deb-54b8-5a40-b49c-e068d5291da1
       - Role: ContextProcessor
       - FQCN: abc.Template_path
       - Node Semantic ID: none
       - Component type: ContextProcessor
       - Input data type: None
       - Output data type: None
       - Parameters from pipeline configuration: None
       - Parameters from processor defaults: None
       - Parameters from context: result (from Node 3)
       - Context additions: path
       - Context suppressions: None
       - Invalid parameters:
       - Configuration valid: True

   Node 5: FloatTxtFileSaver (FloatTxtFileSaver_DataSinkNode)
       - UUID: 64fc72ee-a080-5af4-a771-e200df5b071b
       - Role: DataSink
       - FQCN: semantiva.examples.test_utils.FloatTxtFileSaver
       - Node Semantic ID: none
       - Component type: DataSink
       - Input data type: FloatDataType
       - Output data type: FloatDataType
       - Parameters from pipeline configuration: None
       - Parameters from processor defaults: None
       - Parameters from context: path (from Node 4)
       - Context additions: None
       - Context suppressions: None
       - Invalid parameters:
       - Configuration valid: True

   Footnotes:
   [FloatValueDataSource]
   Outputs a FloatDataType value.

   [FloatAddOperation]
   Add a constant to FloatDataType data.

   [FloatCollectValueProbe]
   A probe that collects the value of the input.

   [Template_path]
   Builds a string from template 'result_{result}.txt' and writes it to context key 'path'.

   [FloatTxtFileSaver]
   Saves a float value in a text file.

For full details on inspection, see :doc:`inspection` and :doc:`ser`.

Where to go next
----------------

- For the full YAML configuration schema, see
  :doc:`architecture/pipeline_schema`.
- For the programmatic, Python-centric view used in R&D, see
  :doc:`pipelines_python`.
- For component and probe contracts, see :doc:`contracts`.
