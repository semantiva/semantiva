Registry & Extensions
=====================

Purpose
-------

- Discover and resolve processors, support **class resolvers** and **parameter resolvers**.

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

Resolvers
---------

- Class resolvers: e.g. ``slicer:``, ``rename:``, ``delete:``
- Parameter resolvers: e.g. ``model:`` for model instantiation

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

