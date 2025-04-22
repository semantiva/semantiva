from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Callable, Any


class SemantivaExecutor(ABC):
    """
    Abstracts how a single data processor executes its internal work.
    """

    @abstractmethod
    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        """
        Submit a callable to be executed asynchronously."""
        pass


class SequentialSemantivaExecutor(SemantivaExecutor):
    """
    Default executor: runs tasks synchronously in the local thread.
    """

    class _ImmediateFuture(Future):
        def __init__(self, result: Any):
            super().__init__()
            self.set_result(result)

    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        result = fn(*args, **kwargs)
        return SequentialSemantivaExecutor._ImmediateFuture(result)
