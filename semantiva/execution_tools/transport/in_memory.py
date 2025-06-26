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
In-process transport implementation for Semantiva that stores messages in memory.
Ideal for local development, testing, or single-machine demos without external dependencies.

This transport supports:
  - Wildcard channel subscriptions using Unix shell-style patterns (fnmatch).
  - Synchronous and asynchronous iteration over matching messages.
  - Optional callback-based consumption in a background thread.
  - No-op acknowledgments and connect/close methods, since it's all in-process.
"""

import threading
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Callable
from concurrent.futures import Future
from fnmatch import fnmatch
from semantiva.context_processors import ContextType

from .base import SemantivaTransport, Subscription, Message


class InMemorySubscription(Subscription):
    """
    Subscription for in-memory channels matching a given pattern.

    Iterates over queued Message objects whose channel name matches the
    provided pattern (supports '*' wildcards). Once all matching messages
    are drained, the iterator exits. Calling close() stops iteration early.
    """

    def __init__(self, queues: Dict[str, tuple[deque, threading.Lock]], pattern: str):
        """
        Args:
            queues:   Shared mapping of channel -> (deque of Message, Lock)
            pattern:  Channel pattern to match (exact name or wildcard)
        """
        self._queues = queues
        self._pattern = pattern
        self._closed = False

    def __iter__(self):
        """
        Blocking iterator over matching messages.

        Yields:
            Message: next queued message whose channel matches the pattern.

        Terminates when:
          - close() is called, or
          - no more matching messages remain in any queue.
        """
        while not self._closed:
            found = False
            # Scan all channels for matches
            for channel, (q, lock) in list(self._queues.items()):
                if fnmatch(channel, self._pattern):
                    with lock:
                        msg = q.popleft() if q else None
                    if msg:
                        found = True
                        yield msg
                        break  # yield one message at a time
            # If no message found for this pattern, exit
            if not found:
                break

    async def __aiter__(self):
        """
        Asynchronous iterator fallback.

        Yields the same messages as the synchronous iterator, but in an async context.
        """
        for msg in self:
            yield msg

    def close(self) -> None:
        """
        Stop the subscription. Subsequent iterations will terminate.
        """
        self._closed = True


class InMemorySemantivaTransport(SemantivaTransport):
    """
    In-memory transport that implements the SemantivaTransport API.

    - Maintains per-channel queues of Message objects.
    - publish() appends to the appropriate queue.
    - subscribe() returns an InMemorySubscription for pattern-based consumption.
    - connect()/close() are no-ops, provided for API symmetry.
    """

    def __init__(self) -> None:
        # channel -> (deque of Message, threading.Lock)
        self._queues: Dict[str, tuple[deque, threading.Lock]] = defaultdict(
            lambda: (deque(), threading.Lock())
        )
        self._connected = False

    def connect(self) -> None:
        """
        Establish the transport.

        No real connection needed for in-memory; sets an internal flag.
        """
        self._connected = True

    def close(self) -> None:
        """
        Tear down the transport.

        No real cleanup needed for in-memory; clears the internal flag.
        """
        self._connected = False

    def publish(
        self,
        channel: str,
        data: Any,
        context: ContextType,
        metadata: Optional[Dict[str, Any]] = None,
        require_ack: bool = False,
    ) -> Optional[Future]:
        """
        Publish a Message to a channel.

        Args:
            channel:     Channel name (string).
            data:        Payload for the message.
            context:     Context dictionary accompanying data.
            metadata:    Optional metadata dict (defaults to {}).
            require_ack: If True, returns a completed Future to simulate ack.

        Returns:
            Future if require_ack=True, else None.
        """
        q, lock = self._queues[channel]
        msg = Message(
            data=data,
            context=context,
            metadata=metadata or {},
            ack=lambda: None,  # No-op ack for in-memory
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
        """
        Subscribe to messages matching the given channel pattern.

        Args:
            channel:  Channel name or wildcard pattern (e.g., "jobs.*.cfg").
            callback: Optional function to call for each incoming Message.
                      If provided, a background thread is started that
                      iterates and invokes callback(msg).

        Returns:
            InMemorySubscription instance for manual iteration if no callback,
            or a subscription with callback-driven background thread.
        """
        sub = InMemorySubscription(self._queues, channel)

        if callback:
            # Launch a daemon thread that pushes each Message to the callback
            def _runner():
                for msg in sub:
                    callback(msg)

            t = threading.Thread(target=_runner, daemon=True)
            t.start()

        return sub
