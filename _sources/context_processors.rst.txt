Context Processors
==================

Context processors implement **context-only logic**. They are responsible for
creating and updating context keys, but they never see the full context object
directly and they never touch the data channel.

High-level model
----------------

At runtime, a context processor is invoked roughly as follows:

1. The node builds the pipeline graph and resolves parameters
   (node configuration > context > defaults).
2. The node constructs a validating context observer.
3. The node calls ``processor.operate_context(context, context_observer, **params)``.
4. The processor executes its internal logic and uses notifier hooks to propose
   context updates or deletions.
5. The observer validates and applies those changes to the active context.

The key points for authors:

- You **do not override** ``process`` / ``operate_context``.
- You **never receive** the context object as a user-facing argument.
- You implement a stateless ``_process_logic`` method and use notifier helpers
  such as ``_notify_context_update`` and ``_notify_context_deletion``.
- You declare which context keys you may create or suppress so that validation
  and inspection can remain deterministic.

Minimal example
---------------

A typical pattern looks like this:

.. code-block:: python

   from semantiva.context_processors import ContextProcessor

   class ComputeLearningRate(ContextProcessor):
       """Derive learning rate from batch size."""

       @classmethod
       def get_created_keys(cls) -> set[str]:
           # Keys this processor may create
           return {"training.learning_rate"}

       def _process_logic(self, *, batch_size: int, base_lr: float = 0.1):
           # ``batch_size`` and ``base_lr`` are resolved by Semantiva from
           # node parameters and/or context; no Context object is passed in.
           lr = base_lr / max(batch_size, 1)
           self._notify_context_update("training.learning_rate", lr)

Notes:

- Parameters from YAML (for example ``base_lr: 0.05``) are not passed through
  the constructor; they are resolved and injected into ``_process_logic``.
- Any context value read by the processor is resolved into a parameter as well
  (here: ``batch_size``).
- All writes go through ``_notify_context_update`` / ``_notify_context_deletion``
  and are validated by the context observer.

YAML configuration
------------------

In a pipeline, the corresponding node might look like:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: ComputeLearningRate
         parameters:
           base_lr: 0.05
           batch_size: 128  # may also come from context

The parameter resolution rules are the same as for data processors:

- Node parameters
- Then context
- Then default values from the function signature

Design guidelines
-----------------

- Keep context processors **small and composable**.
- Use clear, namespaced keys (for example ``training.learning_rate``).
- Declare created/suppressed keys via ``get_created_keys`` /
  ``get_suppressed_keys`` so that observers can validate behaviour.
- Use context processors to prepare domain-specific state; keep data processors
  focused on computations over the data channel itself.

For deeper architectural details, see :doc:`architecture/context_processing`.
