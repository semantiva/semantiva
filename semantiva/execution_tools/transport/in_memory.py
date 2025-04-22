import threading
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Callable
from concurrent.futures import Future
from fnmatch import fnmatch

from .base import SemantivaTransport, Subscription, Message


class InMemorySubscription(Subscription):
    def __init__(self, queues: Dict[str, tuple[deque, threading.Lock]], pattern: str):
        self._queues = queues
        self._pattern = pattern
        self._closed = False

    def __iter__(self):
        """
        Iterate over messages whose channel matches the subscription pattern.
        Supports exact matches (no wildcard) and wildcard patterns using '*'.
        Terminates when no more matching messages are queued.
        """
        while not self._closed:
            found = False
            # Check each channel for matching pattern
            for channel, (q, lock) in list(self._queues.items()):
                if fnmatch(channel, self._pattern):
                    with lock:
                        if q:
                            msg = q.popleft()
                        else:
                            msg = None
                    if msg:
                        found = True
                        yield msg
                        break  # yield one message at a time
            if not found:
                break

    async def __aiter__(self):
        # Fallback to sync iterator
        for msg in self:
            yield msg

    def close(self):
        self._closed = True


class InMemorySemantivaTransport(SemantivaTransport):
    def __init__(self) -> None:
        # map channel -> (deque of Message, Lock)
        self._queues: Dict[str, tuple[deque, threading.Lock]] = defaultdict(
            lambda: (deque(), threading.Lock())
        )
        self._connected = False

    def connect(self) -> None:
        """No-op for in-memory transport."""
        self._connected = True

    def close(self) -> None:
        """No-op for in-memory transport."""
        self._connected = False

    def publish(
        self,
        channel: str,
        data: Any,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        require_ack: bool = False,
    ) -> Optional[Future]:
        """
        Publish a Message to the given channel.
        """
        q, lock = self._queues[channel]
        msg = Message(
            data=data, context=context, metadata=metadata or {}, ack=lambda: None
        )
        with lock:
            q.append(msg)

        if require_ack:
            fut: Future = Future()
            fut.set_result(None)
            return fut
        return None

    def subscribe(
        self, channel: str, *, callback: Optional[Callable[[Message], None]] = None
    ) -> Subscription:
        """Subscribe to channels matching the given pattern."""
        sub = InMemorySubscription(self._queues, channel)

        if callback:
            # Start background thread pushing to callback
            def _runner():
                for msg in sub:
                    callback(msg)

            t = threading.Thread(target=_runner, daemon=True)
            t.start()
        return sub
