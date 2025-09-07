Data IO (Sources & Sinks)
=========================

Overview
--------

Data IO classes define how data flows into and out of pipelines:

- **DataSource** / **PayloadSource**: bring data into the pipeline
- **DataSink** / **PayloadSink**: output data from the pipeline

When wrapped as nodes in a pipeline, these classes are automatically converted to
DataOperation processors with explicit parameter signatures.

**Important**: All IO method parameters must be explicitly declared. `**kwargs` is not allowed
for reliable provenance tracking and parameter validation.

Public API Surface
------------------

- :py:class:`semantiva.data_io.data_io.DataSource`
- :py:class:`semantiva.data_io.data_io.PayloadSource`
- :py:class:`semantiva.data_io.data_io.DataSink`

Autodoc
-------

.. automodule:: semantiva.data_io.data_io
   :members:
   :undoc-members:
   :show-inheritance:
