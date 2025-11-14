Data Processors
===============

Data processors implement the **domain logic** of your pipeline. They transform
data in the payload and may emit new context information, while remaining
fully traceable.

What is a data processor?
-------------------------

A data processor is a subclass of the core *data processor* base class. It
typically:

- Declares its input and output data types.
- Implements a ``process`` method.
- Is registered so it can be referenced from YAML.

Example: simple arithmetic processor
------------------------------------

This example shows the essence of a data processor without context interaction.

.. code-block:: python

   from semantiva.data_types import BaseDataType

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper."""

   class AddConstant:
       """Add a constant value to a float."""

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType

       def __init__(self, addend: float = 0.0):
           self._addend = float(addend)

       def process(self, data: FloatDataType) -> FloatDataType:
           return FloatDataType(data.data + self._addend)

Use in YAML:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: AddConstant
         parameters:
           addend: 2.0

Context-aware data processors
-----------------------------

Some data processors also **notify context updates**. For example, a probe may
compute a summary and store it under a context key:

.. code-block:: python

   from semantiva.core import ContextType

   class MeanProbe:
       """Compute the mean and write to context."""

       @classmethod
       def input_data_type(cls):
           return FloatCollectionDataType

       def __init__(self, context_key: str):
           self.context_key = context_key

       def process(self, data, context: ContextType):
           mean_value = sum(data.values) / len(data.values)
           context.set_value(self.context_key, mean_value)
           return data  # probes usually forward the data unchanged

When you execute such a processor **outside** a pipeline, you can still call
``process`` directly, but you must provide a context object yourself.

Inside a pipeline:

- Context updates are gated by the pipeline configuration.
- Required context keys are validated during inspection and validation.
- Probes without a ``context_key`` will fail validation.

Design guidelines
-----------------

- Keep processors **pure** with respect to arguments:
  configuration goes into parameters, not global state.
- Use data types to encode contracts; avoid passing raw dictionaries where
  a dedicated type would be clearer.
- Do not accept arbitrary ``**kwargs`` in your processor constructors; this
  hinders validation and introspection.
- Use :command:`semantiva dev lint` to enforce contracts and catch violations
  early (see :doc:`contracts`).

For more advanced examples, including collection processors and utility
components, see:

- :doc:`utility_processors`
- :doc:`collection_modifiers`
