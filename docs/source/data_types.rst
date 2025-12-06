Data Types
==========

Data types are the **vocabulary** of your pipelines. They wrap raw Python
objects (numbers, arrays, records, images…) into small, explicit classes that
encode shape, units and semantics.

When every processor declares which data types it expects and produces, whole
pipelines become easier to reason about and easier to validate.

What is a data type?
--------------------

A data type is a subclass of ``BaseDataType``. It is a thin wrapper around a
Python value with a well-defined meaning.

Key properties:

- It encapsulates a single piece of data (``.data``).
- It documents **what the value *means*** (units, bounds, interpretation).
- It can enforce invariants through a ``validate`` hook.

Conceptually:

.. code-block:: python

   from semantiva.data_types import BaseDataType

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper used in examples."""

       def validate(self, data: float) -> bool:
           if not isinstance(data, float):
               raise TypeError("Data must be a float")
           return True

   value = FloatDataType(1.0)
   print("value:", value.data)
   print("repr:", value)

.. code-block:: console

   value: 1.0
   repr: FloatDataType(1.0)

In this example:

- ``FloatDataType`` is the semantic carrier: “this is a float used inside
  a Semantiva pipeline”.
- The underlying value is available via ``.data``.
- The ``validate`` method is the hook for enforcing additional invariants.


BaseDataType API
----------------

All data types inherit from ``BaseDataType``. The
core API is:

- ``__init__(self, data, logger=None)`` - constructs the type, calls
  ``validate`` on the value and then stores it internally.
- ``data`` property - gets or sets the underlying value.
- ``validate(self, data) -> bool`` - hook for subclasses to enforce
  invariants.
- ``__str__`` / ``__repr__`` - by default display
  ``ClassName(<data-repr>)``.

The typical pattern is:

1. **Subclass** ``BaseDataType[T]`` with a concrete ``T`` (for example
   ``float``, ``str``, an array type, a record type).
2. **Override** ``validate`` to check invariants for that type.
3. Avoid overriding ``__init__``; let ``BaseDataType`` own construction
   so that introspection, metadata and SVA rules remain consistent.

Example: positive float
-----------------------

Sometimes you want to express a stronger invariant than “any float”. For
example, “this value must be strictly positive”. The correct place to encode
this is **in the data type**, not as ad-hoc checks scattered across
processors.

Here is a minimal ``PositiveFloat`` implementation that enforces
positivity via ``validate``:

.. code-block:: python

   from semantiva.data_types import BaseDataType

   class PositiveFloat(BaseDataType[float]):
       """Strictly positive scalar float."""

       def validate(self, data: float) -> bool:
           # BaseDataType.__init__ will call this before storing ``data``.
           if data <= 0.0:
               raise ValueError(f"{data} is not positive")
           return True

   ok = PositiveFloat(1.5)
   print("ok:", ok)

   # This will raise a ValueError at construction time:
   try:
       bad = PositiveFloat(0.0)
   except ValueError as exc:
       print("error:", exc)

.. code-block:: console

   ok: PositiveFloat(1.5)
   error: 0.0 is not positive

Notes:

- The invariant “strictly positive” is attached to the **type**, not to a
  specific processor or function.
- Any processor that declares ``input_data_type() -> PositiveFloat`` is saying
  “I expect a strictly positive scalar float”, which is much clearer than
  accepting a plain ``float`` and relying only on docstrings.
- Because we implemented the check in ``validate`` and did not override
  ``__init__``, we keep the construction behaviour of ``BaseDataType``
  intact.


Using data types in processors
------------------------------

Data types become most useful when processors and pipelines use them
consistently.

A typical data operation will:

- Declare its ``input_data_type`` and ``output_data_type``.
- Accept instances of those types in its ``process`` method.
- Return a new instance of the output type.

For example, consider a simple addition operation that works on floats:

.. code-block:: python

   from semantiva.data_types import BaseDataType
   from semantiva.data_processors.data_processors import DataOperation

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper (as above)."""

       def validate(self, data: float) -> bool:
           if not isinstance(data, float):
               raise TypeError("Data must be a float")
           return True


   class FloatAddOperation(DataOperation):
       """Add a constant to FloatDataType data."""

       def _process_logic(self, data, addend: float):
           return FloatDataType(data.data + addend)

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType


   # Example usage
   value = FloatDataType(1.0)
   op = FloatAddOperation()
   result = op.process(value, addend=2.0)

   print("input:", value)
   print("result:", result)

.. code-block:: console

   input: FloatDataType(1.0)
   result: FloatDataType(3.0)

This combination of types and operations is what gives Semantiva pipelines
their semantic clarity:

- ``BaseDataType`` defines **how** to create and validate values.
- Concrete types like ``FloatDataType`` and ``PositiveFloat``
  express domain-specific invariants.
- Data operations declare which types they consume and produce, making
  pipelines easier to inspect, validate and evolve.

Next steps
----------

- See :doc:`data_operations` for more on data operations.
- See :doc:`data_probes` for read-only probes that derive metrics from data.

