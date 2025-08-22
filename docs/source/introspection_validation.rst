Introspection & Validation
==========================

- Build inspections, summarize, export JSON, validate.

Examples
--------

.. code-block:: python

   from semantiva.inspection.reporter import json_report
   # Assume p is a Pipeline instance
   report = json_report(p)
   print(report)

Autodoc
-------

.. automodule:: semantiva.inspection.builder
   :members:
   :undoc-members:

.. automodule:: semantiva.inspection.reporter
   :members:
   :undoc-members:

.. automodule:: semantiva.inspection.validator
   :members:
   :undoc-members:
