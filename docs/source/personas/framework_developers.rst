Framework developers & component authors
========================================

This page is for people who **extend Semantiva itself**:

- You write or maintain **DataOperation**, **DataProbe** and **ContextProcessor**
  classes.
- You care about **contracts, SVA rules and linting**, not just whether a
  pipeline runs.
- You may also contribute to the core framework or build internal libraries
  on top of Semantiva.

If you mainly run and tweak existing pipelines, see
:doc:`pipeline_users` instead.

For a programmatic view of pipelines while you design and test components,
see :doc:`../pipelines_python`. For how those pipelines are expressed and
governed in production, see :doc:`../pipelines_yaml`.

.. admonition:: New to Semantiva?

   If you have never run a Semantiva pipeline before, **start with**
   :doc:`../getting_started` and then follow :doc:`pipeline_users`.

   Come back to this page once you are comfortable reading pipeline YAML and
   running existing pipelines.

------------------------------
What you should know already
------------------------------

Before you use this page as your main guide, you should:

- Have followed :doc:`../getting_started` and :doc:`pipeline_users`.
- Be comfortable with:

  - Writing Python code, including classes and type hints.
  - Running tests (e.g. with ``pytest``) from the command line.
  - Editing and running Semantiva pipeline YAMLs.

- Have a rough idea that:

  - A pipeline is a **graph** of nodes that wrap processors.
  - Execution operates on a **payload** with both data and context.
  - Probes and context keys are important for inspection and debugging.

If any of that sounds unfamiliar, revisit :doc:`../getting_started`,
:doc:`pipeline_users` and :doc:`../concepts` first.

------------------------------
Your learning path (201+)
------------------------------

Once you are comfortable as a pipeline user, this is the recommended path for
**framework developers and component authors**.

Step 1 - Confirm the mental model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a component author, you must internalise a few architectural invariants:

- The **dual-channel** design (data vs context).
- The role of **nodes** and **context observers**.
- The separation between **data processors** and **context processors**.

To solidify this, (re)read:

- :doc:`../concepts` - focus on payloads, processors and nodes.
- :doc:`../architecture/context_processing` - how context processors and
  observers work.
- :doc:`../pipelines_python` - how processors are wired into nodes during
  development.
- :doc:`../pipelines_yaml` - how the same wiring appears in production
  YAML.

You do **not** need to understand every internal implementation detail, but you
do need to be clear about:

- Processors implementing business logic.
- Nodes and observers owning context access and mutations.

Step 2 - Learn how to author components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, read :doc:`../creating_components` as your **authoring guide**. Treat it
as the canonical reference for:

- When to use **DataOperation**, **DataProbe** and **ContextProcessor**.
- How to implement ``_process_logic`` for each type.
- Which metadata to declare (``input_data_type``, ``output_data_type``,
  ``get_created_keys``, etc.).

Keep the following in mind as you read and implement your first component:

- ``_process_logic`` on all component types works with **parameters and data**;
  it should **not** take the context object directly.
- Probes are **read-only**: they observe data and return a value; nodes decide
  whether and where to store that value in context.
- Context processors use ``operate_context`` and notifier helpers to update
  context via observers.

Step 3 - Deepen your understanding of processor families
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have written one or two components, use these pages as deeper
references:

- :doc:`../data_operations` - details of data operations and patterns.
- :doc:`../data_probes` - details of read-only probes.
- :doc:`../context_processors` - details of context-only processors and their
  lifecycle.
- :doc:`../collection_modifiers` - utilities for working with collections as
  part of your processors.
- :doc:`../utility_processors` - examples of smaller helper components.

At this stage you should be able to:

- Recognise patterns you can reuse.
- Check how built-in components declare types and context keys.
- Model your own components after “good citizen” examples.

Step 4 - Work with contracts, SVA rules and linting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a framework developer, you are expected to **keep contracts green**:

- Read :doc:`../contracts` to understand:

  - What SVA rules are.
  - How ``semantiva dev lint`` enforces contracts, including rules like
    ``SVA250`` that protect processor signatures.

- Consult the full catalog in :doc:`../contracts` (via the included
  ``contracts_catalog``) when you need details about a specific rule.

In your daily workflow you should:

- Run ``semantiva dev lint`` when you add or modify components.
- Treat SVA violations as design feedback, not just as “red tests”.

Step 5 - Learn development & testing practices around Semantiva
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To integrate your components into a robust development process, use:

- :doc:`../development/testing_strategies` - how to write tests that exercise
  pipelines, components and inspection.
- :doc:`../cli` - sections describing developer-facing commands (inspection,
  linting, running tests).
- :doc:`../logger` - how logging is handled in Semantiva and how your
  components should emit logs when needed.

You do **not** need to memorise every CLI option or test pattern. Instead, treat
these pages as a toolbox you consult while working on components and their
pipelines.

-----------------------------------------
Working effectively with contracts & SVA
-----------------------------------------

Semantiva's contracts are designed to make it **hard to do the wrong thing** by
accident. As a component author, you should lean on them:

- Use :doc:`../contracts` to understand the rules that apply to your
  components, especially:

  - Rules for declaring ``input_data_type`` / ``output_data_type``.
  - Rules about context key metadata (e.g. ``get_created_keys``).
  - Rules that constrain how processors relate to context and probes.

- When ``semantiva dev lint`` reports a violation:

  - Use the SVA code to jump into the catalog in :doc:`../contracts`.
  - Follow the :ref:`sva-troubleshooting-workflow` to resolve the issue and
    rerun the linter.
  - Adjust your design or metadata rather than silencing the rule.

If you find yourself repeatedly fighting a contract, that is usually a sign
that:

- A conceptual invariant needs to be clarified in docs, or
- A new rule / exception should be proposed, not bypassed.

----------------------------------------------
Common tasks and where to look in the docs
----------------------------------------------

This section is a quick **router** for common authoring tasks and where to find
the relevant documentation.

Implement a new DataOperation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** create a processor that transforms data and may produce new
  context keys.
- **Look at:**
  - :doc:`../creating_components` (DataOperation section and examples).
  - :doc:`../data_operations` (existing DataOperation implementations).
  - :doc:`../contracts` (contracts that apply to data operations).

Implement a new DataProbe
~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** compute metrics or summaries from data, optionally storing
  them in context via nodes.
- **Look at:**
  - :doc:`../creating_components` (probe authoring guidelines).
  - :doc:`../data_probes` (existing probes and patterns).
  - :doc:`../pipelines_yaml` (probe nodes and ``context_key`` behaviour in production).
  - :doc:`../pipelines_python` (probe wiring in development workflows).
  - :doc:`../contracts` (probe-related SVA rules).

Implement a new ContextProcessor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** implement logic that adjusts context (e.g. configuration,
  state) between data-processing steps.
- **Look at:**
  - :doc:`../creating_components` (ContextProcessor section).
  - :doc:`../context_processors` (behaviour, lifecycle and examples).
  - :doc:`../architecture/context_processing` (observer pattern and invariants).
  - :doc:`../contracts` (ContextProcessor-specific rules).

Integrate a new component into a pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** expose your new component to pipeline users.
- **Look at:**

  - :doc:`../pipelines_yaml` (how processors are referenced and configured in
    YAML).
  - :doc:`../data_types` and :doc:`../data_collections`
    (to ensure the types you expect are reflected in pipeline definitions).
  - :doc:`../inspection` and :doc:`../run_space` (to verify behaviour in traces).

Troubleshoot lint failures or contract violations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** understand and fix issues reported by ``semantiva dev lint``.
- **Look at:**

  - :doc:`../contracts` (meaning of the SVA code you see).
  - :doc:`../introspection_validation` (how introspection and validation work).
  - :doc:`../development/testing_strategies` (adding tests around the failing
    behaviour).

Expose data to Semantiva Studio Viewer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** ensure your components and pipelines emit traces that can be
  explored in Studio Viewer or similar tools.
- **Look at:**

  - :doc:`../inspection` (what is recorded and how).
  - :doc:`../ser` and :doc:`../run_space_emission` (how execution is captured).
  - :doc:`../studio_viewer` (how Studio Viewer consumes traces and SER).
