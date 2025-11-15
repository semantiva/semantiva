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

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   getting_started
   tutorials/run_space_quickstart
   examples_index

.. toctree::
   :maxdepth: 1
   :caption: User guide

   concepts
   pipeline
   data_types
   data_collections
   data_processors
   collection_modifiers
   context_processors
   data_io
   run_space
   utility_processors
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
   :caption: Extensibility & architecture

   extensions
   creating_components
   workflows_fitting_models
   architecture/context_processing
   architecture/pipeline_schema
   architecture/registry
   studio_viewer

.. toctree::
   :maxdepth: 1
   :caption: Reference

   contracts
   api_reference
   logger
   exceptions
   glossary
   development/testing_strategies

Index & search
--------------

* :ref:`genindex` — Global index of terms and pages
* :ref:`modindex` — Python module index
* :ref:`search` — Full-text search
