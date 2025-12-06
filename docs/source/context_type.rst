Context Type
============

The context channel carries structured metadata alongside your data. It is
represented by :class:`semantiva.core.ContextType` and is part of every
:class:`semantiva.core.Payload`.

In user code, you rarely manipulate the context directly - pipeline nodes and
observers usually do this for you. However, it is useful to understand how
the context behaves.

Creating and using a context
----------------------------

.. code-block:: python

   from semantiva.core import ContextType

   ctx = ContextType()

   # Store values
   ctx.set_value("threshold", 0.5)
   ctx.set_value("run.label", "demo")

   # Retrieve them
   print("threshold:", ctx.get_value("threshold"))
   print("label:", ctx.get_value("run.label"))

.. code-block:: console

   # [agent-fill-output: run the snippet; show the printed threshold and label]

Context values are used for:

- Parameters injected into operations (for example an ``addend`` or a path).
- Metrics and probe results stored during execution.
- Flags or small pieces of state that guide downstream behaviour.

Context and payload
-------------------

The context always travels together with the data inside a
:class:`semantiva.core.Payload`:

.. code-block:: python

   from semantiva.core import Payload

   payload = Payload(data="example", context=ctx)
   print(payload.data)
   print(payload.context.get_value("threshold"))

.. code-block:: console

   # [agent-fill-output: run the snippet; show the printed values]

**Important invariant**

User-defined components (data operations, data probes, context processors)
do **not** receive :class:`ContextType` directly in their business logic.
They see parameters, and nodes/observers perform the actual context
updates.

Next steps
----------

- Continue with :doc:`pipeline` for a Python-level view of how payload and
  context move through nodes.
