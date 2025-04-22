from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Iterator, AsyncIterator, NamedTuple
from concurrent.futures import Future


class Message(NamedTuple):
    data: Any
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    ack: Callable[[], None]  # call to acknowledge receipt


class Subscription(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Message]:
        """Blocking iterator of incoming messages."""
        ...

    @abstractmethod
    async def __aiter__(self) -> AsyncIterator[Message]:
        """Async iterator of incoming messages."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Unsubscribe / stop listening."""
        ...


class SemantivaTransport(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Initialize any client / server resources."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Tear down connections, stop background threads."""
        ...

    @abstractmethod
    def publish(
        self,
        channel: str,
        data: Any,
        context,
        metadata: Optional[Dict[str, Any]] = None,
        require_ack: bool = False,
    ) -> Optional[Future]:
        """
        Send a message to `channel`.
        If require_ack=True, return a Future that completes when the message
        is durably accepted (or raises on error).
        """

    @abstractmethod
    def subscribe(
        self, channel: str, *, callback: Optional[Callable[[Message], None]] = None
    ) -> Subscription:
        """
        Begin listening to `channel`. If callback is provided, each incoming
        Message is delivered to it; otherwise you can iterate over the returned
        Subscription (sync or async) to pull messages manually.
        """
