Data Probes
===========

Data probes are **read-only observers** of the data channel. They compute a
value from the input data and return it. Probes do not modify the data or
the context directly.

In pipelines, probe results are typically written into the context by the
node that wraps the probe, using a ``context_key``. The probe itself remains
completely context-agnostic.

What is a data probe?
---------------------

A data probe is a subclass of
:class:`semantiva.data_processors.data_processors.DataProbe`. It:

- Declares a single ``input_data_type`` class method.
- Implements ``_process_logic(self, data, **params) -> Any``.
- Does **not** declare an ``output_data_type`` (SVA231 warns against it).

Example: mean of a float collection
-----------------------------------

.. code-block:: python

   from semantiva.data_processors.data_processors import DataProbe
   from semantiva.examples.test_utils import FloatDataCollection, FloatDataType

   class MeanProbe(DataProbe):
       """Compute the mean of a :class:`FloatDataCollection`."""

       @classmethod
       def input_data_type(cls):
           return FloatDataCollection

       def _process_logic(self, data: FloatDataCollection) -> float:
            values = [item.data for item in data]
            return sum(values) / max(len(values), 1)

   probe = MeanProbe()
   collection = FloatDataCollection(
       [FloatDataType(1.0), FloatDataType(2.0), FloatDataType(3.0), FloatDataType(4.0)]
   )
   mean_value = probe(collection)
   print("mean:", mean_value)

.. code-block:: console

   mean: 2.5

Using probes in pipelines
-------------------------

Inside a pipeline, a node wraps a probe and takes care of writing its
result into the context when ``context_key`` is provided. The probe does
not see the context object at all.

For example, in YAML you would configure a node like:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: my.probes.MeanProbe
         context_key: "mean_value"

The node injects the probe result under ``"stats.mean"`` using a context
observer. The probe remains a pure function of its input data and parameters.

(The full pipeline wiring and CLI usage is covered later in :doc:`pipeline`.)

Design guidelines
-----------------

- Keep probes small and focused on single metrics or summaries.
- Prefer returning plain Python values (floats, dicts, small dataclasses).
- Never read or write the context directly from a probe.
- Use :command:`semantiva dev lint` to ensure the ``DataProbe`` contracts
  (``SVA230``–``SVA232``) are satisfied.

Next steps
----------

- Continue with :doc:`data_io` to see how data enters and leaves pipelines.
