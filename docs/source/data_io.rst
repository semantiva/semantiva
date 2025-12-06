Data I/O: sources and sinks
===========================

Data I/O components connect Semantiva pipelines to the outside world:

- **Sources** produce typed data from files, databases or other systems.
- **Sinks** consume typed data and write it to disk, sockets, viewers or
  external services.

Both are regular Semantiva components with clear type contracts.

Sources
-------

A data source typically declares an ``output_data_type`` (``SVA200``) and
no ``input_data_type``. It encapsulates how raw external data is loaded and
wrapped into a suitable data type.

Example (conceptual):

.. code-block:: python

   from pathlib import Path
   from semantiva.data_types import BaseDataType
   from semantiva.data_processors.data_processors import DataOperation

   class FloatDataType(BaseDataType[float]):
       """Scalar float value."""

   class ToyFloatSource(DataOperation):
       """Load a float from a text file (conceptual example)."""

       @classmethod
       def input_data_type(cls):
           # Sources are often wrapped by factories; this example keeps the
           # signature simple and uses ``None`` at call time.
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType

       def _process_logic(self, data: FloatDataType, path: str) -> FloatDataType:
           value = float(Path(path).read_text().strip())
           return FloatDataType(value)

   # In a real pipeline this would be wrapped and called by a node.
   source = ToyFloatSource()
   result = source(FloatDataType(0.0), path="input.txt")
   print(result.data)

.. code-block:: console

   # [agent-fill-output: create a simple input.txt, run the snippet and show the loaded value]

Sinks
-----

A data sink declares an ``input_data_type`` (``SVA210``) and typically does
not declare an ``output_data_type``. It takes a typed value and writes it to
an external target.

.. code-block:: python

   class ToyFloatSink(DataOperation):
       """Write a float to a text file (conceptual example)."""

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           # Many sinks use a pass-through output type; we do the same here.
           return FloatDataType

       def _process_logic(self, data: FloatDataType, path: str) -> FloatDataType:
           Path(path).write_text(str(data.data))
           return data

   sink = ToyFloatSink()
   out = sink(FloatDataType(3.0), path="output.txt")
   print(out.data)

.. code-block:: console

   # [agent-fill-output: run the snippet; confirm the value is written and printed]

In real projects you will rarely implement I/O operations by hand - you will
use extensions such as :mod:`semantiva_imaging` or project-specific
components. The examples above are deliberately minimal to illustrate the
type contracts.

Next steps
----------

- Read :doc:`context_type` to see how context values are managed.
- Then move on to :doc:`pipeline` to see how all pieces are combined.
