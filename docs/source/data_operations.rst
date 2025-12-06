Data Operations
===============

Data operations implement the **domain logic** of your pipeline on the data
channel. They transform input data types into output data types while
remaining fully traceable and context-agnostic.

What is a data operation?
-------------------------

A data operation is a subclass of
:class:`semantiva.data_processors.data_processors.DataOperation`. It:

- Declares its ``input_data_type`` and ``output_data_type`` as
  class methods.
- Implements ``_process_logic(self, data, **params)`` with the business
  logic.
- Optionally declares metadata such as ``get_created_keys`` for contracts.

User logic lives in ``_process_logic``, not in the constructor.

Example: simple arithmetic operation
------------------------------------

This example shows a minimal operation that adds a constant to a float.

.. code-block:: python

   from semantiva.data_types import BaseDataType
   from semantiva.data_processors.data_processors import DataOperation

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper used in user-guide examples."""

   class FloatAddOperation(DataOperation):
       """Add a constant to :class:`FloatDataType` data."""

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType

       @classmethod
       def get_created_keys(cls) -> list[str]:
           """Declare context keys created by this operation (none here)."""
           return []

       def _process_logic(self, data: FloatDataType, addend: float) -> FloatDataType:
           return FloatDataType(data.data + addend)

   op = FloatAddOperation()
   result = op(FloatDataType(1.0), addend=2.0)
   print(result.data)

.. code-block:: console

   3.0

Note how ``addend`` is a *runtime parameter* to ``_process_logic`` - it is
**not** passed through the constructor. Constructors should remain simple
and parameter-free so that pipelines and registries can instantiate
components deterministically.

Context invariants
------------------

Data operations never receive the ``ContextType`` object
directly in ``process`` or ``_process_logic``. They operate on data plus
parameters only.

When used inside a pipeline, any interaction with the context is mediated
by nodes and context observers:

- Nodes resolve runtime parameters from configuration and the payload
  context.
- Nodes and observers are responsible for writing results into context.

The SVA contract ``SVA220`` enforces that every data operation declares both
its input and output data types. See :doc:`contracts` for the full catalog.

Outside pipelines, you can still call a data operation directly, exactly as
in the example above.

.. code-block:: python

   payload_value = FloatDataType(10.0)
   op = FloatAddOperation()
   print(op(payload_value, addend=0.5))

.. code-block:: console

   FloatDataType(10.5)

Next steps
----------

- See :doc:`data_probes` for read-only probes.
- See :doc:`data_io` for data sources and sinks.
