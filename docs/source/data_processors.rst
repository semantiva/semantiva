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

.. admonition:: Context invariants

   - Data processors (``DataOperation`` and ``DataProbe``) never take
     ``ContextType`` directly as a parameter. Their ``process``/``_process_logic``
     methods operate on **data only** plus resolved runtime parameters.
   - All context reads and writes are mediated by pipeline nodes and context
     observers attached to the payload.

Context-aware probes (via nodes)
--------------------------------

A probe computes a value from the data channel and *returns* it. When the
pipeline node specifies ``context_key``, the node writes the probe result into
context on behalf of the probe.

.. code-block:: python

   from semantiva.data_processors.data_processors import DataProbe
   from semantiva.examples.test_utils import FloatCollectionDataType

   class MeanProbe(DataProbe):
       """Compute the mean of a collection; context-agnostic."""

       @classmethod
       def input_data_type(cls) -> type:
           return FloatCollectionDataType

       def _process_logic(self, data: FloatCollectionDataType) -> float:
           return sum(data.values) / max(len(data.values), 1)

In YAML, configure the probe node with a ``context_key``:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: my.probes.MeanProbe
         context_key: "stats.mean"

At runtime, the node wraps ``MeanProbe`` in a probe context injector node and
uses a context observer to store the returned value under ``stats.mean``. The
``MeanProbe`` component itself never receives or mutates the context.

Outside pipelines, you can still call ``process`` directly and handle the
returned value yourself, but you remain responsible for any storage.

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
