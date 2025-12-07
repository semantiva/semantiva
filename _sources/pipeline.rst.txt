Pipelines in Semantiva
======================

Pipelines orchestrate data operations, probes, sources, sinks and context
processors into a coherent execution graph.

Semantiva supports two complementary ways to work with pipelines:

- **YAML & CLI (production)** – pipelines are defined declaratively in
  YAML and executed via the :command:`semantiva` CLI. This is the
  **canonical, production-grade configuration artefact**.
- **Python (development & R&D)** – pipelines are constructed directly
  in Python for rapid prototyping, testing, and learning.

Choose your path:

- If you are a **pipeline user or operator**, start with
  :doc:`pipelines_yaml`.
- If you are a **framework developer or component author**, see
  :doc:`pipelines_python`.

The rest of the documentation assumes that **production pipelines are
defined in YAML**, even when examples are shown in Python for clarity
or experimentation.
