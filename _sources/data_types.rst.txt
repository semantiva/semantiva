Data Types
==========

Semantiva data types are **contracts** for the data channel. Each type
describes the expected shape, units, and semantics of the payloads that flow
through a pipeline. These contracts let the pipeline builder and the runtime
reason about compatibility between nodes and provide predictable execution.

At a high level:

- :py:class:`~semantiva.data_types.data_types.BaseDataType` is the common
   base for all concrete data types.
- :py:class:`~semantiva.data_types.data_types.DataCollectionType` models
   ordered collections of elements that share the same base type (see also
   :doc:`data_collections`).
- :py:class:`~semantiva.data_types.data_types.NoDataType` is used when a
   processor operates purely on context or side effects and does not carry
   domain data.

Public API Surface
------------------

- :py:class:`semantiva.data_types.data_types.BaseDataType`
- :py:class:`semantiva.data_types.data_types.DataCollectionType`
- :py:class:`semantiva.data_types.data_types.NoDataType`

Autodoc
-------

.. automodule:: semantiva.data_types.data_types
   :members:
   :undoc-members:
   :show-inheritance:
