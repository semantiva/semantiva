Semantiva Documentation
=======================

Semantiva is a semantic execution framework for **typed, traceable, inspectable**
pipelines.

This documentation is organised by **role** and **experience level**:

- Start with *Getting started* if you are new to Semantiva.
- Use the *User guide* for day-to-day pipeline work.
- Use *Tracing & identity* when you care about provenance and inspection.
- Use *Extensibility & architecture* when authoring components or integrating Semantiva.
- Use *Reference* for exception types, glossary entries and low-level details.

.. admonition:: Where to start

   - New to Semantiva? Start with :doc:`getting_started`, then see :doc:`personas/pipeline_users`.
   - Writing or maintaining processors? See :doc:`personas/framework_developers`.
   - Integrating Semantiva into a wider system? See :doc:`personas/architects_system_designers`.

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   getting_started

.. toctree::
   :maxdepth: 1
   :caption: Persona entry points

   personas/pipeline_users
   personas/framework_developers
   personas/architects_system_designers

.. toctree::
   :maxdepth: 1
   :caption: User guide

   concepts
   data_types
   data_operations
   data_probes
   data_io
   context_type
   pipeline
   data_collections
   collection_modifiers
   utility_processors
   run_space
   context_processors
   cli

.. toctree::
   :maxdepth: 1
   :caption: Tracing, identity & inspection

   ser
   schema_semantic_execution_record_v1
   trace_stream_v1
   trace_aggregator_v1
   trace_graph_alignment
   identity_cheatsheet
   graph
   inspection
   introspection_validation
   run_space_emission
   run_space_lifecycle
   execution

.. toctree::
   :maxdepth: 1
   :caption: Component authoring & architecture

   creating_components
   architecture/overview
   extensions
   workflows_fitting_models
   architecture/context_processing
   architecture/pipeline_schema
   architecture/registry
   studio_viewer

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/run_space_quickstart

.. toctree::
   :maxdepth: 1
   :caption: Reference

   contracts
   api_reference
   logger
   exceptions
   glossary
   examples_index
   development/testing_strategies

Index & search
--------------

* :ref:`genindex` — Global index of terms and pages
* :ref:`modindex` — Python module index
* :ref:`search` — Full-text search
