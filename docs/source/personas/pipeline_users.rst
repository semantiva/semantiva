Pipeline users
==============

This page is for people who **run and tweak Semantiva pipelines**:

- You work primarily with *pipeline YAMLs* and *contexts*, not with Semantiva internals.
- You care about **what** a pipeline does, how to configure it, and how to **inspect results**.
- You may occasionally add a simple probe or swap a processor, but authoring new components is not your main focus.

If you want to write new components or change Semantiva itself, see
:doc:`../personas/framework_developers` or
:doc:`../personas/architects_system_designers` instead.

As a pipeline user, your primary reference for day-to-day work is
:doc:`../pipelines_yaml`. You normally do not need to construct pipelines
in Python; that pathway (:doc:`../pipelines_python`) is mainly for
framework developers and advanced R&D workflows.

.. admonition:: New to Semantiva?

   If you have never run a Semantiva pipeline before, **start with**
   :doc:`../getting_started`. It walks you through running your first pipeline
   from the command line and explains the basic workflow.

   Come back to this page once you have successfully run at least one example
   pipeline.

------------------------------
What you should know already
------------------------------

Before you use this page as your main guide, you should:

- Have followed :doc:`../getting_started` and run at least one example pipeline.
- Be comfortable with:
  - Executing commands from a terminal (shell, PowerShell, etc.).
  - Editing YAML files in your editor of choice.
- Have a rough idea that a Semantiva pipeline:

  - Is a **graph** of nodes, each wrapping a processor.
  - Operates on a **payload** with both data and context.
  - Can emit traces / run records that you can inspect later.

If any of that sounds unfamiliar, revisit :doc:`../getting_started` and
:doc:`../concepts` first.

-------------------------
Your learning path (101)
-------------------------

Once you have completed the basic getting started example, this is the
recommended path for **pipeline users**.

Step 1 – Understand core concepts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read :doc:`../concepts` with the mindset:

- *“I am a pipeline user, not a framework developer.”*
- Focus especially on:

  - **Payload** (data vs context).
  - **Pipeline nodes** and how they wrap processors.
  - The idea of **probes** vs **operations**.

You do **not** need to understand every internal detail on first read; the goal
is to have names for the core building blocks you will see in YAML.

Step 2 – Know your data building blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before wiring nodes, skim the core building blocks so YAML labels make sense:

- :doc:`../data_types` — building blocks for individual data items.
- :doc:`../data_operations` — transformations that declare input/output types.
- :doc:`../data_probes` — read-only probes that surface metrics or summaries.
- :doc:`../data_io` — sources and sinks for moving data into and out of Semantiva.
- :doc:`../context_type` — how metadata travels alongside data.
- :doc:`../data_collections` — how to represent sequences / collections.

You can skim these once and return when you see unfamiliar types or processors
in a pipeline definition.

Step 3 – Learn the pipeline YAML model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, read :doc:`../pipelines_yaml` as your **pipeline user guide**:

- Concentrate on:

  - The `pipeline:` and `nodes:` sections in YAML.
  - How you reference processors by dotted path.
  - How node-level configuration works (including ``context_key`` for probes).
  - How parameters are resolved from configuration and context.

You do not need to understand extension points or advanced inspection yet; treat
this page as the “language reference” for pipeline YAML.

Step 4 – Explore the pipeline user toolbox
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you are comfortable reading pipeline YAML, you will often ask:

- *“Which processors can I reuse?”*
- *“Is there a built-in component for this?”*

Use these pages as your toolbox index:

- :doc:`../data_operations` — core data operations you can plug into pipelines.
- :doc:`../data_probes` — probes that compute metrics or summaries.
- :doc:`../collection_modifiers` — helpers for working with data collections.
- :doc:`../context_processors` — processors that operate on context only (useful
  when you need to adjust configuration or state between data steps).
- :doc:`../utility_processors` — miscellaneous processors that do not fit the
  main categories.
- :doc:`../data_io` — components for reading and writing data.

As a pipeline user, you typically:

- **Reuse** these processors as-is.
- Configure them in YAML.
- Rely on contracts & lints (:doc:`../contracts`) to tell you if you miswired
  something.

Step 5 – Learn the CLI surface you actually need
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For day-to-day use, most pipeline users only need a subset of Semantiva’s CLI:

- :doc:`../cli` — for details and examples.

Focus on:

- Running pipelines (``semantiva run`` and related commands).
- Running inspections / validations before execution.
- Running tests or checks that are relevant in your environment.

You do **not** need to learn every CLI command; treat this page as a reference
you can return to when needed.

-------------------------------------------------
From pipelines to inspection and troubleshooting
-------------------------------------------------

Once you are comfortable running pipelines and reading YAML, the next step is:

- *“How do I see what actually happened?”*
- *“How do I debug when something looks wrong?”*

Semantiva has rich inspection and trace capabilities. As a pipeline user, you
mainly care about:

- **Whether a pipeline executed as expected.**
- **Which context values and probe results were produced.**
- **Where in the pipeline something went wrong.**

To go deeper into this:

1. Start with :doc:`../inspection` for the big picture of how Semantiva records
   and exposes execution information.
2. When you need more detail, use:

   - :doc:`../ser` — high-level overview of the Semantic Execution Record.
   - :doc:`../run_space` — how multiple runs and variations are organised.
   - :doc:`../run_space_lifecycle` — how runs are created, updated and closed.

You do not need to memorise the SER schema or trace stream formats; treat them
as **reference** that you consult when debugging complex behaviour or when using
external tooling like Semantiva Studio Viewer.

----------------------------------------------
Common tasks and where to look in the docs
----------------------------------------------

This section is a quick “router” for common tasks you will perform as a pipeline
user and where to find the relevant documentation.

Run an existing pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** execute a pipeline someone else defined.
- **Look at:**
  - :doc:`../getting_started` (for the basic command-line pattern).
  - :doc:`../pipelines_yaml` (for understanding the YAML layout).
  - :doc:`../cli` (for CLI options relevant to running pipelines).

Modify a parameter or context value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** adjust configuration or context used by a pipeline.
- **Look at:**
  - :doc:`../pipelines_yaml` (node configuration and parameter resolution).
  - :doc:`../context_processors` (if the pipeline uses dedicated context logic).
  - :doc:`../run_space` (when you are exploring many runs with differing inputs).

Inspect probe outputs and context keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** see metrics or summaries produced by probes.
- **Look at:**
  - :doc:`../pipelines_yaml` (probe nodes and ``context_key`` behaviour).
  - :doc:`../data_probes` (probe components used in the pipeline).
  - :doc:`../inspection` and :doc:`../ser` (how to view results in traces).

Understand why a pipeline failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** debug an error or unexpected result.
- **Look at:**
  - :doc:`../inspection` (how to navigate inspection tools).
  - :doc:`../exceptions` (common Semantiva exceptions and what they mean).
  - :doc:`../introspection_validation` (how validation highlights misconfigurations).

Explore more advanced workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** go beyond single runs, e.g. parameter sweeps or model fitting.
- **Look at:**
  - :doc:`../tutorials/run_space_quickstart`
  - :doc:`../workflows_fitting_models`
  - :doc:`../run_space` and :doc:`../run_space_lifecycle`
