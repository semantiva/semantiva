Glossary
========

.. glossary::

   Pipeline
     The ordered execution of factory-generated nodes wrapping processors.

   Node
     A factory-generated wrapper (users do not subclass nodes).

   Processor
     A single-responsibility unit of computation (DataOperation, DataProbe, IO, ContextProcessor).

   Data Type
     Contract object declaring input/output types (e.g., BaseDataType, DataCollectionType, NoDataType).

   Context
     Execution key/value store with safe mutation (required/created/suppressed keys).

   Payload
     The envelope passed between nodes during execution, carrying both
     ``data`` (typed value) and ``context`` (metadata dictionary with
     required/created/suppressed keys). Pipelines always return a Payload
     when executed.

   Resolver
     Mechanism to resolve classes/parameters from YAML (e.g., ``slicer:``, ``rename:``, ``model:``).

   Studio Viewer
     Read-only UI for YAML pipeline visualization.
