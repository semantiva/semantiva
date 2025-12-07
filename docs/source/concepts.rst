Basic Concepts
==============

Semantiva narrows the gap between ideas and executable pipelines. It is built
around **typed payloads**, a **dual data/context channel**, and clear contracts
for every processor.

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

For a deeper tour of data types and validation patterns, see :doc:`data_types`.


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

See :doc:`data_operations` and :doc:`creating_components` for more examples of
declaring and wiring data operations.


Data probes: read-only observers
--------------------------------

Data probes are processors that **observe** data and return a value. They
never mutate the data; in a pipeline, the node that wraps a probe typically
injects the observed value into the context when it is configured with a
``context_key``. The probe itself stays unaware of context, keeping the
business logic simple and reusable.

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

See :doc:`data_probes` and :doc:`creating_components` for more on probe
contracts and usage patterns.


Context types: structured metadata
----------------------------------

Semantiva represents the context channel with ``ContextType``, a small
mapping-like container for per-run metadata. Context keys can hold
configuration parameters, derived values, tags used for bookkeeping, and
indicators such as data-quality scores or validation flags, and can be 
used to track and coordinate behaviour over the life of a run.

.. code-block:: python

  from semantiva import ContextType

  context = ContextType()
  context.set_value("experiment.id", "exp-001")
  context.set_value("example.addend", 2.0)

  print(context)
  print("addend:", context.get_value("example.addend"))

.. code-block:: console

  ContextType(context={'experiment.id': 'exp-001', 'example.addend': 2.0})
  addend: 2.0

ContextType is central to how pipelines share state across nodes, but most
user code treats it as an opaque mapping. See :doc:`context_type` and
:doc:`context_processors` for details on context semantics and management.


Payload: combining data and context
-----------------------------------

Every Semantiva pipeline step processes a *payload* with two channels:

- **Data channel** - typed domain objects wrapped in data types.
- **Context channel** - structured metadata carried alongside the data.

At any point in a run you can think of the payload as a simple pair that
combines data and context:

.. code-block:: python

  from semantiva import ContextType, Payload
  from semantiva.examples import FloatDataType

  context = ContextType()
  context.set_value("example.addend", 2.0)

  payload = Payload(
     data=FloatDataType(1.0),
     context=context,
  )

  print("data:", payload.data)
  print("context:", payload.context)

.. code-block:: console

   data: FloatDataType(1.0)
   context: ContextType(context={'example.addend': 2.0})

Nodes pass ``Payload`` objects between steps, but processors themselves only
see the data value and explicit parameters. Nodes and pipeline infrastructure
mediate between business logic and the context channel.

Context is treated as a protected space: updates flow through context
processors and observer hooks so that changes can be validated and traced.

Payloads and their role in execution are discussed further in
:doc:`pipeline`, :doc:`pipelines_yaml` and :doc:`pipelines_python`.


Nodes and pipelines
-------------------

At a high level, Semantiva's execution model looks like this:

1. A pipeline is a **graph of nodes**.
2. Each node wraps a **processor** (data operation, probe, context processor,
   source or sink) and controls how it sees the payload.
3. Processors declare their data contracts via data types and their expected
   context keys via contracts.
4. Optional trace drivers observe execution and emit Semantic Execution
   Records (SER) (see :doc:`ser`).

Semantiva has a parameter resolution mechanism: node parameters may be
provided by the YAML configuration, processor defaults, or the payload
context, with well-defined precedence rules. Nodes are responsible for
resolving these parameters, unpacking the payload, calling processors with
data only, and applying any configured context updates. See
:doc:`pipelines_yaml`, :doc:`pipelines_python` and
:doc:`introspection_validation` for details.

SER records are produced by trace drivers attached to the orchestrator and
executor and do not change data or context.

From a user perspective:

- You **define processors** in Python (see :doc:`creating_components`).
- You **configure production pipelines** declaratively in YAML
  (see :doc:`pipelines_yaml`), which serves as the **configuration
  artefact of record**.
- The same execution model can be exercised directly in Python for
  **development, R&D and notebook workflows** (see
  :doc:`pipelines_python`), but Python pipelines are not treated as
  system-of-record configuration.
- You **execute** via :doc:`cli` or the Python API, always working with the
  payload abstraction.


Run space: multiple runs from one spec
--------------------------------------

Run space lets you describe a family of runs (for example, parameter sweeps)
in a single YAML configuration by adding a ``run_space`` block. The CLI
expands this specification into individual runs that share a run-space
configuration ID while each run has its own run ID.

See :doc:`run_space` and :doc:`tutorials/run_space_quickstart` for a guided
walkthrough of run-space configuration and lifecycle.


Context processors
------------------

Context processors work primarily on the **context** channel. They read values
from context, apply some transformation, and request updates via observer
hooks; nodes and context observers handle the actual mutations.

A minimal example is a context-only pipeline that renames a key from
``"input_key"`` to ``"output_key"``. Use the shorthand ``rename:src:dst``
syntax to define context processors inline:

.. code-block:: python

   from semantiva import ContextType, Payload, Pipeline

   # Single-node pipeline with rename context processor
   nodes = [
       {
           "processor": "rename:input_key:output_key",
       },
   ]

   pipeline = Pipeline(nodes)

   # Create context with "input_key" and process through pipeline
   context = ContextType({"input_key": "hello"})
   payload = Payload(data=None, context=context)
   result = pipeline.process(payload)
   print("output context:", result.context)

.. code-block:: console

   output context: ContextType(context={'output_key': 'hello'})

Other built-in context processors follow the same idea and can be created
with similar shorthand syntax:

- ``delete:some.key`` creates a context processor that deletes a key.
- ``template:"result_{value}.txt":path`` creates a template-based processor
  that combines existing context keys into a new string.

See :doc:`context_processors` for a complete reference to context processors,
including composition patterns for enrichment and routing.


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
   parameters: OrderedDict([('addend', float)])

   semantic id:

   ========  SEMANTIC ID  ========
   Class Name: FloatAddOperation
   ===============================
    - Docstring:
       Add a constant to FloatDataType data.
    - component_type: DataOperation
    - parameters:
       addend: float
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

For more on how component identities participate in pipeline and execution
inspection, see :doc:`identity_cheatsheet` and :doc:`inspection`.


Semantic Execution Records
--------------------------

Tracing is an optional layer that records how pipelines execute over time.

- **Semantic Execution Records (SER)** capture which processors ran, how they
  were connected, and summary information about payloads and context at each
  step.
- **Trace drivers** attach to the orchestrator and executor. They observe
  execution events and write SER streams, typically to files or external
  sinks.

Trace drivers are configured in the pipeline YAML (see
:doc:`architecture/pipeline_schema`) and described in more detail in
:doc:`ser`, :doc:`trace_stream_v1`, :doc:`trace_graph_alignment` and
:doc:`schema_semantic_execution_record_v1`.
