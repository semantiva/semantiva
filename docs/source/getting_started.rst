Getting Started
===============

.. admonition:: Who this is for

   This page is for people who are **completely new to Semantiva**.
   You do not need any prior knowledge of Semantiva, but you should be
   comfortable running commands in a terminal and editing small text files.

   After completing this page, continue with :doc:`personas/pipeline_users`.

This page walks you from **installation** to running your **first pipeline**.

Install Semantiva
-----------------

Semantiva requires Python 3.10+.

Install from PyPI:

.. code-block:: bash

   pip install semantiva

Then verify that the CLI is available:

.. code-block:: bash

   semantiva --help

.. code-block:: console

   usage: semantiva [-h] [--version] {run,inspect,dev} ...

   positional arguments:
     {run,inspect,dev}
       run              Execute a pipeline from a YAML file
       inspect          Inspect a pipeline configuration from a YAML file
       dev              Developer tools

   options:
     -h, --help         show this help message and exit
     --version          show program's version number and exit

The three main subcommands are ``run``, ``inspect``, and ``dev``.
Common usage patterns:

.. code-block:: bash

   # Execute a pipeline
   semantiva run pipeline.yaml

   # With context values
   semantiva run pipeline.yaml --context key=value

   # Validate before running
   semantiva run pipeline.yaml --validate

   # Inspect pipeline configuration
   semantiva inspect pipeline.yaml

   # Extended inspection with per-node details
   semantiva inspect pipeline.yaml --extended

The ``dev`` subcommand is primarily for framework developers; 
:command:`semantiva dev lint` audits components against the 
:doc:`Semantiva Contracts <contracts>` catalog. For full options 
and advanced usage, see :doc:`cli`. For detailed inspection examples
and validation workflows, see :doc:`introspection_validation` and 
:doc:`pipelines_yaml`.

Quickstart - Hello pipeline (YAML only)
---------------------------------------

The smallest useful example is a pipeline defined purely in YAML and executed
from the CLI. Create a file ``hello.yaml``:

.. code-block:: yaml

   extensions: ["semantiva-examples"]  # or your own extension packages

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: FloatAddOperation
         parameters: {}

       - processor: FloatCollectValueProbe
         context_key: "result"

       - processor: template:"result_{result}.txt":path

       - processor: FloatTxtFileSaver

Note that ``FloatAddOperation`` has no ``addend`` parameter in the configuration;
it will be provided via context at runtime.

Run the pipeline, supplying ``addend=2.0`` via context:

.. code-block:: bash

  semantiva run hello.yaml --context addend=2.0

.. code-block:: console

   2025-12-06 20:31:04,935 - INFO     - ▶️  Run 1/1 starting (__init__)
   2025-12-06 20:31:04,935 - INFO     - Starting pipeline with 5 nodes (pipeline)
   2025-12-06 20:31:04,938 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 20:31:04,938 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.003291s; Elapsed CPU Time: 0.003290s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000063s;    Elapsed Wall Time: 0.000063s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000048s;    Elapsed Wall Time: 0.000048s
                   Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000039s;    Elapsed Wall Time: 0.000039s
                   Node 4: Template_path;  Elapsed CPU Time: 0.000041s;    Elapsed Wall Time: 0.000041s
                   Node 5: FloatTxtFileSaver;      Elapsed CPU Time: 0.000186s;    Elapsed Wall Time: 0.000186s
    (pipeline)
   2025-12-06 20:31:04,938 - INFO     - ✅ Run 1/1 completed in 0.00s (__init__)
   2025-12-06 20:31:04,938 - INFO     - Output data: FloatDataType(3.0) (__init__)
   2025-12-06 20:31:04,938 - INFO     - Output context:
     addend: 2.0
     result: 3.0
     path: 'result_3.0.txt' (__init__)

The probe node writes into the context key ``result``, which is used to define
the output file path in the following context processor. The last node saves the
final float value to that file.

Running the same pipeline from Python
-------------------------------------

You can run the same configuration programmatically. The **pipeline
configuration** is still the single source of truth - your Python code just
loads and executes it.

.. code-block:: python

  from semantiva import ContextType, Payload, Pipeline, load_pipeline_from_yaml

  nodes = load_pipeline_from_yaml("hello.yaml")
  pipeline = Pipeline(nodes)

  context = ContextType()
  context.set_value("addend", 2.0)
  payload = Payload(data=None, context=context)
  result = pipeline.process(payload)

  print(result.context.get_value("result"))

.. code-block:: console

  2025-12-06 20:31:05,007 - INFO     - Starting pipeline with 5 nodes (pipeline)
  2025-12-06 20:31:05,011 - INFO     - Pipeline execution complete. (pipeline)
  2025-12-06 20:31:05,011 - INFO     - Pipeline execution report:

          Pipeline Calls: 1; Elapsed Wall Time: 0.004379s; Elapsed CPU Time: 0.004376s
                  Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000074s;    Elapsed Wall Time: 0.000075s
                  Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000050s;    Elapsed Wall Time: 0.000050s
                  Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000045s;    Elapsed Wall Time: 0.000045s
                  Node 4: Template_path;  Elapsed CPU Time: 0.000044s;    Elapsed Wall Time: 0.000044s
                  Node 5: FloatTxtFileSaver;      Elapsed CPU Time: 0.000280s;    Elapsed Wall Time: 0.000281s
   (pipeline)
  Context addend: 2.0
  Result: 3.0

Run-space: multiple runs from one definition
--------------------------------------------

Instead of calling the CLI in a loop with different ``--context`` values,
you can describe a *grid* of runs using a ``run_space`` block in the same
YAML file.

A minimal example uses the same pipeline as ``hello.yaml``. Create a file ``run_space_demo.yaml``:

.. code-block:: yaml

   extensions: ["semantiva-examples"]

   run_space:
     combine: combinatorial
     max_runs: 20
     dry_run: false
     blocks:
       - mode: by_position
         context:
           addend: [1.0, 2.0]

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: FloatAddOperation
         parameters: {}

       - processor: FloatCollectValueProbe
         context_key: "result"

       - processor: template:"result_{result}.txt":path

       - processor: FloatTxtFileSaver

Then:

.. code-block:: bash

   semantiva run run_space_demo.yaml

.. code-block:: console

   2025-12-06 20:31:05,344 - INFO     - ▶️  Run 1/2 starting (__init__)
   2025-12-06 20:31:05,344 - INFO     - Starting pipeline with 5 nodes (pipeline)
   2025-12-06 20:31:05,347 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 20:31:05,347 - INFO     - Pipeline execution report:

           Pipeline Calls: 1; Elapsed Wall Time: 0.003650s; Elapsed CPU Time: 0.003648s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000072s;    Elapsed Wall Time: 0.000072s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000056s;    Elapsed Wall Time: 0.000056s
                   Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000046s;    Elapsed Wall Time: 0.000046s
                   Node 4: Template_path;  Elapsed CPU Time: 0.000048s;    Elapsed Wall Time: 0.000048s
                   Node 5: FloatTxtFileSaver;      Elapsed CPU Time: 0.000236s;    Elapsed Wall Time: 0.000236s
    (pipeline)
   2025-12-06 20:31:05,348 - INFO     - ✅ Run 1/2 completed in 0.00s (__init__)
   2025-12-06 20:31:05,348 - INFO     - Output data: FloatDataType(2.0) (__init__)
   2025-12-06 20:31:05,348 - INFO     - Output context:
     addend: 1.0
     result: 2.0
     path: 'result_2.0.txt' (__init__)
   2025-12-06 20:31:05,348 - INFO     - ▶️  Run 2/2 starting (__init__)
   2025-12-06 20:31:05,348 - INFO     - Starting pipeline with 5 nodes (pipeline)
   2025-12-06 20:31:05,353 - INFO     - Pipeline execution complete. (pipeline)
   2025-12-06 20:31:05,353 - INFO     - Pipeline execution report:

           Pipeline Calls: 2; Elapsed Wall Time: 0.008541s; Elapsed CPU Time: 0.008539s
                   Node 1: FloatValueDataSource;   Elapsed CPU Time: 0.000089s;    Elapsed Wall Time: 0.000089s
                   Node 2: FloatAddOperation;      Elapsed CPU Time: 0.000075s;    Elapsed Wall Time: 0.000075s
                   Node 3: FloatCollectValueProbe;         Elapsed CPU Time: 0.000052s;    Elapsed Wall Time: 0.000053s
                   Node 4: Template_path;  Elapsed CPU Time: 0.000069s;    Elapsed Wall Time: 0.000069s
                   Node 5: FloatTxtFileSaver;      Elapsed CPU Time: 0.000297s;    Elapsed Wall Time: 0.000297s
    (pipeline)
   2025-12-06 20:31:05,353 - INFO     - ✅ Run 2/2 completed in 0.01s (__init__)
   2025-12-06 20:31:05,353 - INFO     - Output data: FloatDataType(3.0) (__init__)
   2025-12-06 20:31:05,353 - INFO     - Output context:
     addend: 2.0
     result: 3.0
     path: 'result_3.0.txt' (__init__)

Semantiva will expand the blocks into individual runs, each with a concrete
set of context keys. In this example:

- **Run 1** receives ``addend=1.0``, producing ``1.0 + 1.0 = 2.0`` and saving to ``result_2.0.txt``.
- **Run 2** receives ``addend=2.0``, producing ``1.0 + 2.0 = 3.0`` and saving to ``result_3.0.txt``.

All runs share a **run-space configuration ID** and
each run has its own **run ID**, which you can see in the trace stream.

CSV-driven run-spaces and more advanced patterns are covered in
:doc:`tutorials/run_space_quickstart`.

Next steps
----------

For a deeper understanding of the model:

- :doc:`concepts` — Basic concepts and the dual data/context channel
- :doc:`pipeline` — Pipelines and nodes
- :doc:`cli` — CLI usage patterns

When you care about provenance and inspection, continue with:

- :doc:`ser`
- :doc:`trace_stream_v1`
