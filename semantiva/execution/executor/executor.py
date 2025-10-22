# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Defines the SemantivaExecutor abstraction and a default synchronous implementation.
Executors encapsulate how individual pipeline tasks (node processing) are run,
decoupling the orchestration logic from the actual execution strategy.

This abstraction allows Semantiva to support multiple execution models:
  - Synchronous (SequentialSemantivaExecutor)
  - Thread- or process-based pools
  - Distributed task frameworks (Ray, Dask, Celery, etc.)

An executor's submit() returns a Future, enabling orchestrators to
track and compose asynchronous results uniformly.
"""

from abc import ABC, abstractmethod
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Callable, Any, Optional


class SemantivaExecutor(ABC):
    """Abstract base for Semantiva task executors."""

    @dataclass
    class SERHooks:
        """Execution record hook bundle used by executors.

        A container of metadata providers and evidence that an executor may
        attach to a task invocation for tracing and validation. Fields include
        upstream dependency ids, the trigger label, upstream evidence blobs,
        and callables providing context deltas, pre/post checks, environment
        pins, and redaction policies.
        """

        upstream: list[str]
        trigger: str
        upstream_evidence: list[dict]
        context_delta_provider: Callable[[], Any] | None
        pre_checks: list[Any]
        post_checks_provider: Callable[[], list[Any]] | None
        env_pins_provider: Callable[[], dict] | None
        redaction_policy_provider: Callable[[], dict] | None

    @abstractmethod
    def submit(
        self,
        fn: Callable[..., Any],
        *args,
        ser_hooks: Optional["SemantivaExecutor.SERHooks"] = None,
        **kwargs,
    ) -> Future:
        """Submit a callable for (possibly asynchronous) execution."""
        pass


class SequentialSemantivaExecutor(SemantivaExecutor):
    """
    Default, local executor that runs each task synchronously in the calling thread.

    This implementation is useful for simple use cases, debugging, or
    environments without a distributed runtime. It fulfills the
    SemantivaExecutor contract by immediately executing the callable
    and returning an already-completed Future.
    """

    class _ImmediateFuture(Future):
        """A Future already completed with a provided result.

        Used by the synchronous executor to present a uniform Future-based
        API while executing callables immediately in the caller thread.
        """

        def __init__(self, result: Any):
            """
            Initialize and immediately set the Future's result.

            Args:
                result: The value to store in the Future.
            """
            super().__init__()
            self.set_result(result)

    def submit(
        self,
        fn: Callable[..., Any],
        *args,
        ser_hooks: Optional[SemantivaExecutor.SERHooks] = None,
        **kwargs,
    ) -> Future:
        """
        Execute the function immediately and return a completed Future.

        Args:
            fn:   The function or callable to execute synchronously.
            *args/**kwargs: Arguments for the function.

        Returns:
            A completed Future whose result() returns fn(*args, **kwargs).
        """
        # ser_hooks is accepted for API parity with async executors.
        # Directly call the function in the current thread
        result = fn(*args, **kwargs)
        # Wrap the result in an ImmediateFuture so callers can uniformly
        # use Future.result() even in synchronous mode
        return SequentialSemantivaExecutor._ImmediateFuture(result)
