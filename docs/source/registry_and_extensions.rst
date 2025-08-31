Registry & Extensions
=====================

Semantiva discovers and resolves processors via a registry that supports
**class resolvers** and **parameter resolvers**. This page shows how to extend
Semantiva with custom types and operations and how the registry locates them.

Extension Quickstart
--------------------

This example adds a domain-specific ``DataType`` and a ``DataOperation`` that
computes GC content for DNA sequences.

.. code-block:: python

   # mypkg/bio.py
   from semantiva.data_types import BaseDataType
   from semantiva.data_processors import DataOperation

   class DNASequence(BaseDataType):
       """Domain data type representing a DNA sequence."""
       def __init__(self, data: str):
           super().__init__(data)
           if not set(data) <= {"A", "C", "G", "T"}:
               raise ValueError("Invalid DNA string; allowed: A,C,G,T")

   class GCContentOperation(DataOperation[DNASequence, DNASequence]):
       """Compute GC fraction and return a short string result in a DNASequence."""
       def _operation(self, data: DNASequence) -> DNASequence:
           seq = data.data
           gc = (seq.count("G") + seq.count("C")) / max(1, len(seq))
           return DNASequence(f"GC={gc:.2f}")

Programmatic usage (note the :term:`Payload` return):

.. code-block:: python

   from semantiva.pipeline import Pipeline
   from mypkg.bio import DNASequence, GCContentOperation

   p = Pipeline([GCContentOperation()])
   result = p.process()  # -> :term:`Payload`
   # In a real pipeline the upstream node would create the DNASequence.
   # For a minimal demo, call the operation's inner function directly:
   out = GCContentOperation()._operation(DNASequence("ACGT"))
   assert out.data.startswith("GC=")

.. important::

   Users do **not** subclass Nodes. Nodes are factory-generated wrappers around
   processors. You extend Semantiva by writing processors (e.g., DataOperation)
   and DataTypes with clear, single-responsibility behavior.

Discovery & Registration
------------------------

Semantiva resolves processors by **fully qualified class name (FQCN)**, or via
the installed registry when short names are available.

**Class import (FQCN)**

If your package is installed and importable, YAML can reference your processor
directly by FQCN:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: mypkg.bio.GCContentOperation

Semantiva imports the class through the Class Registry during pipeline load.

**Plugin loader (programmatic registration)**

You can also register components at startup. The plugin loader scans installed
extensions and/or executes explicit registrations.

.. code-block:: python

   from semantiva.registry.plugin_registry import load_extensions
   load_extensions()  # discover and register installed Semantiva extensions

   # Optional: manual registration pattern (example)
   # from semantiva.registry.class_registry import ClassRegistry
   # from mypkg.bio import DNASequence, GCContentOperation
   # ClassRegistry.register_datatype(DNASequence)
   # ClassRegistry.register_processor(GCContentOperation)

See the API reference for :py:mod:`semantiva.registry.plugin_registry` and
:py:mod:`semantiva.registry.class_registry`.

Referencing Custom Processors in YAML
-------------------------------------

Assuming your package is installed and importable, you can reference the processor
directly in your pipeline:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: mypkg.bio.GCContentOperation
         parameters: {}

The upstream node must produce the expected input ``DataType`` (``DNASequence`` in
this example). Use :doc:`pipeline` to connect processors into complete flows.

Resolvers (class & parameter)
-----------------------------

**Class resolvers** let YAML reference dynamic processors without writing classes:

.. code-block:: yaml

   - processor: "rename:metrics.a:features.a"  # move key
   - processor: "delete:metrics.temp"          # drop key

**Parameter resolvers** normalize special parameter values:

.. code-block:: yaml

   parameters:
     model: "model:PolynomialFittingModel:degree=2"

See :mod:`semantiva.registry.class_registry` for the built-ins: ``rename:``, ``delete:``, ``slicer:``, ``sweep:``, and the ``model:`` parameter resolver.

.. _modeldescriptor:

ModelDescriptor
---------------

A descriptor object describing how to construct a model at realization time
(e.g., ``model:PolynomialFittingModel:degree=2``). See :ref:`objects-in-pipeline-configurations`.

.. _plan-then-realize-optional:

Plan then realize (optional)
----------------------------

Factories may first **plan** nodes (validate/spec) and later **realize** them (materialize classes).
This two-step pattern aids validation and caching but is not required for simple pipelines.

Best Practices
--------------

* **Single responsibility**: each processor should do one thing.
* **Type contracts**: be explicit about input/output DataTypes; validate early.
* **Context discipline**: document required/created/suppressed keys.
* **Docstrings**: write user-facing docstrings; they appear in autodoc and the Viewer.
* **Determinism**: avoid non-deterministic defaults; surface seeds as parameters.
* **Repr safety**: ensure ``__repr__`` is concise or redacted for trace summaries.
* **Performance**: avoid heavy work in constructors; do it in ``_operation``.

Testing Extensions
------------------

Doctest snippet (keeps examples truthful):

.. code-block:: python

   >>> from mypkg.bio import DNASequence, GCContentOperation
   >>> GCContentOperation()._operation(DNASequence("ACGT")).data
   'GC=0.50'

Pytest example:

.. code-block:: python

   def test_gc_content():
       from mypkg.bio import DNASequence, GCContentOperation
       out = GCContentOperation()._operation(DNASequence("GGGG"))
       assert out.data == "GC=1.00"

Packaging & Distribution
------------------------

For Semantiva to resolve your classes by FQCN, your package must be installed
in the environment where pipelines run.

Checklist:

* ``pip install .`` (or publish to an index) so ``import mypkg`` works.
* Keep runtime dependencies minimal and documented.
* Version your extension; follow Semantiva minor versions for compatibility notes.

Security & Resources
--------------------

* **Secrets & PII**: do not place secrets in ``context`` or reprs; store references.
* **Trace exposure**: repr fields may be written to trace summaries; redact as needed.
* **Memory**: free large buffers promptly; prefer streaming when possible.
* **Concurrency**: if using threads/processes, keep processor state re-entrant.

See also
--------

*Semantiva Imaging* demonstrates a larger domain extension with custom image
DataTypes, operations, and I/O components. See its documentation for patterns
that scale beyond a single processor.

Public API Surface
------------------

- :py:class:`semantiva.registry.class_registry.ClassRegistry`
- :py:class:`semantiva.registry.plugin_registry.SemantivaExtension`
- :py:func:`semantiva.registry.plugin_registry.load_extensions`

Descriptors
-----------

Declarative way to reference constructible classes and recursively resolve them.

.. automodule:: semantiva.registry.descriptors
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

.. code-block:: python

   from semantiva.registry import ClassRegistry, load_extensions
   load_extensions()  # load entry-point based extensions if any
   cls = ClassRegistry.get_class("slicer:YourOp:YourCollection")

Autodoc
-------

.. automodule:: semantiva.registry.class_registry
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: semantiva.registry.plugin_registry
   :members:
   :undoc-members:
   :show-inheritance:

