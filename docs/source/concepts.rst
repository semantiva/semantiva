Basic Concepts
==============

Semantiva narrows the gap between ideas and executable pipelines. It is built
around **typed payloads**, a **dual data/context channel**, and clear contracts
for every processor.

The payload: data + context
---------------------------

Every Semantiva pipeline step processes a *payload* with two channels:

- **Data channel** - your domain objects (images, arrays, records, models…).
- **Context channel** - structured metadata that flows with the data through
  the pipeline. It carries configuration parameters, derived values, quality
  indicators, and other state used by processors to share information and
  adapt execution.

At any point in a run you can think of the payload as a simple pair:

.. code-block:: python

   from semantiva import ContextType, Payload

   context = ContextType()
   context.set_value("example.addend", 2.0)

   payload = Payload(
       data="some domain object",
       context=context,
   )

   print("data:", payload.data)
   print("context:", payload.context)

.. code-block:: console

   data: some domain object
   context: ContextType(context={'example.addend': 2.0})

Processors always see the payload, not just the raw data. They can:

- Read and transform the **data** channel.
- Read and update the **context** channel.
- Decide how to behave based on what is already in context (for example,
  reading parameters from context instead of configuration).


Data types: wrapping domain objects
-----------------------------------

Data types are small, typed wrappers around your domain objects. They are
subclasses of ``BaseDataType`` and carry both the raw value and its semantic
contract.

.. code-block:: python

   from semantiva.data_types import BaseDataType

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper used in user-guide examples."""

       def validate(self, data: float) -> bool:
           # Accept any float; processors may add stronger checks.
           return True

   x = FloatDataType(1.5)
   print(x)
   print("value:", x.data)

.. code-block:: console

   FloatDataType(1.5)
   value: 1.5

Why wrap values at all?

- Types make contracts explicit (e.g. “single float” vs “array of floats”).
- Processors can declare exactly which data types they expect and produce.
- Inspection and tracing can show “what kind of thing” is flowing through
  the pipeline instead of just raw Python types.


Data operations: transformations as callables
---------------------------------------------

Data operations are processors that **transform** one data type into another
(or the same type). They subclass
:class:`semantiva.data_processors.data_processors.DataOperation` and declare
their input/output data types.

.. code-block:: python

   from semantiva.data_processors.data_processors import DataOperation
   from semantiva.examples import FloatDataType

   class FloatAddOperation(DataOperation):
       """Add a constant to :class:`FloatDataType` values."""

       @classmethod
       def input_data_type(cls):
           return FloatDataType

       @classmethod
       def output_data_type(cls):
           return FloatDataType

       def _process_logic(self, data: FloatDataType, addend: float) -> FloatDataType:
           return FloatDataType(data.data + addend)

   value = FloatDataType(1.0)

   # Option 1: use the class-level convenience
   result = FloatAddOperation.run(value, addend=2.0)

   # Option 2: instantiate and call
   op = FloatAddOperation()
   result2 = op(value, addend=2.0)

   print("result:", result.data)
   print("result2:", result2.data)

.. code-block:: console

   result: 3.0
   result2: 3.0

Key properties:

- The operation declares both ``input_data_type`` and ``output_data_type``.
- User logic lives in ``_process_logic``.
- Runtime parameters such as ``addend`` are regular keyword arguments to
  ``_process_logic`` / ``process`` / ``run`` - not constructor arguments.
- Instances are callable; ``op(data, **params)`` is equivalent to
  ``op.process(data, **params)``.


Data probes: read-only observers
--------------------------------

Data probes are processors that **observe** data and return a summary value.
They never mutate the data or the context; they just compute and return a
result. Pipelines decide what to do with that result (for example, storing
it in the context under a key).

.. code-block:: python

   from semantiva.data_processors.data_processors import DataProbe
   from semantiva.examples.test_utils import FloatDataCollection, FloatDataType

   class MeanProbe(DataProbe):
       """Compute the mean of a collection."""

       @classmethod
       def input_data_type(cls):
           return FloatDataCollection

       def _process_logic(self, data: FloatDataCollection) -> float:
           values = [item.data for item in data]
           return sum(values) / max(len(values), 1)

   collection = FloatDataCollection(
       [FloatDataType(1.0), FloatDataType(2.0), FloatDataType(3.0), FloatDataType(4.0)]
   )
   probe = MeanProbe()
   mean_value = probe(collection)
   print("mean:", mean_value)

.. code-block:: console

   mean: 2.5

Later, in the pipeline pages, you will see how a probe result becomes part of
the context via a node ``context_key`` - without the probe itself knowing
anything about context.


Context processors and observers
--------------------------------

Context processors and observers work primarily on the **context** channel:

- **Context processors** can read and update context keys. They are used for
  tasks like routing, enrichment, aggregation and cross-node coordination.
- **Context observers** are read-only; they watch for certain conditions in
  the context and may emit warnings, metrics or trace annotations.

From the payload's point of view, they behave like data processors but
operate on different state:

- Data operations focus on ``payload.data``.
- Context processors focus on ``payload.context``.
- Probes read data and return a value; nodes decide whether to send that
  value into the context.


Putting it together: payload, processors, pipelines
---------------------------------------------------

At a high level, Semantiva's execution model looks like this:

1. A pipeline is a **graph of nodes**.
2. Each node wraps a **processor** (data operation, probe, context processor,
   source or sink) and controls how it sees the payload.
3. Processors declare their data contracts via data types and their expected
   context keys via contracts.
4. Optional trace drivers observe execution and emit **Semantic Execution
   Records (SER)**.

Processors and pipeline nodes operate only on the data and context channels.
SER records are produced by trace drivers attached to the orchestrator and
executor and do not change data or context.

From a user perspective:

- You **define processors** in Python (see :doc:`creating_components`).
- You **configure pipelines** in YAML (see :doc:`pipeline`).
- You **execute** via :doc:`cli` or the Python API, always working with the
  payload abstraction.

For a more visual explanation of how all this fits together:

- :doc:`data_types`
- :doc:`data_operations`
- :doc:`data_probes`
- :doc:`context_processors`
- :doc:`data_collections`


Component identity
------------------

Semantiva components (data operations, probes, context processors, data
types, sources, sinks…) all inherit from a common base that provides
**component metadata** and a **semantic identity string**.

At class level, every component can expose its metadata as a dictionary via
``get_metadata`` and as a human-readable string via ``semantic_id``:

.. code-block:: python

   from semantiva.examples import FloatAddOperation

   # Structured metadata as a dictionary
   metadata = FloatAddOperation.get_metadata()
   print("class_name:", metadata["class_name"])
   print("component_type:", metadata.get("component_type"))
   print("parameters:", metadata.get("parameters"))

   # Human-friendly identity string
   print("\nsemantic id:\n")
   print(FloatAddOperation.semantic_id())

.. code-block:: console

   class_name: FloatAddOperation
   component_type: DataOperation
   parameters: OrderedDict([('addend', ParameterInfo(default=<object object at 0x7f9b6eba4b00>, annotation='float'))])

   semantic id:

   ========  SEMANTIC ID  ========
   Class Name: FloatAddOperation
   ===============================
    - Docstring:
       Add a constant to FloatDataType data.
    - component_type: DataOperation
    - parameters:
     addend: ParameterInfo(default=<object object at 0x7f9b6eba4b00>, annotation='float')
    - input_data_type: FloatDataType
    - output_data_type: FloatDataType
   ===============================

Conceptually:

- ``get_metadata()`` gathers base fields (at least ``class_name`` and the
  class docstring) and merges them with component-specific fields provided by
  ``_define_metadata()`` (for example ``component_type``, parameter
  signatures, input/output data type information).
- ``semantic_id()`` formats the same information as a structured, multi-line
  string that is easy to read in logs, dashboards or LLM-based tools. The
  default format includes a header, the class name, the docstring and the
  key metadata fields.
- The metadata and semantic ID are **derived from the class**, not from a
  particular instance, so they describe the component's role and contract
  rather than any single run.

You normally do not need to call these methods when writing pipelines, but
they become invaluable when:

- Inspecting components interactively.
- Debugging mismatched contracts between processors and data types.
- Building tooling on top of Semantiva's metadata model, such as explorers,
  documentation generators or LLM-based helpers.


Trace records and trace drivers
-------------------------------

Tracing is an optional layer that records how pipelines execute over time.

- **Semantic Execution Records (SER)** capture which processors ran, how they
  were connected, and summary information about payloads and context at each
  step.
- **Trace drivers** attach to the orchestrator and executor. They observe
  execution events and write SER streams, typically to files or external
  sinks.

Trace drivers are configured in the pipeline YAML (see
:doc:`architecture/pipeline_schema`) and described in more detail in
:doc:`trace_stream_v1` and :doc:`ser`.


Where to go next
----------------

- Continue with :doc:`data_types` to see how to define and validate custom
  data types.
- Then read :doc:`data_operations` and :doc:`data_probes` to learn how to
  write reusable processors.
