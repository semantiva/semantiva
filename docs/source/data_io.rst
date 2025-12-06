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
   from semantiva import DataSource
   from semantiva.examples import FloatDataType

   class ToyFloatSource(DataSource):
       """Load a float from a text file (conceptual example)."""

       @classmethod
       def _get_data(cls, path: str) -> FloatDataType:
           value = float(Path(path).read_text().strip())
           return FloatDataType(value)

       @classmethod
       def output_data_type(cls):
           return FloatDataType

   # Use the sample file shipped with the documentation.
   result = ToyFloatSource.get_data("docs/examples/data/io_input.txt")
   print(result.data)

.. code-block:: console

   2.5

Sinks
-----

A data sink declares an ``input_data_type`` (``SVA210``) and typically does
not declare an ``output_data_type``. It takes a typed value and writes it to
an external target.

.. code-block:: python

   from pathlib import Path
   from semantiva import DataSink
   from semantiva.examples import FloatDataType

   class ToyFloatSink(DataSink[FloatDataType]):
       """Write a float to a text file (conceptual example)."""

       @classmethod
       def _send_data(cls, data: FloatDataType, path: str) -> None:
           Path(path).write_text(f"{data.data}\n")

       @classmethod
       def input_data_type(cls):
           return FloatDataType

   # Use the sink to write an output file and confirm its contents.
   value = FloatDataType(3.0)
   ToyFloatSink.send_data(value, path="output.txt")
   print(value.data)
   print("file contains:", Path("output.txt").read_text().strip())

.. code-block:: console

   3.0
   file contains: 3.0

In real projects you may implement I/O operations by hand or rely on
extensions such as ``semantiva_imaging`` or project-specific components.
The examples above are deliberately minimal to illustrate the type contracts.

Next steps
----------

- Read :doc:`context_type` to see how context values are managed.
- Then move on to :doc:`pipeline` to see how all pieces are combined.
