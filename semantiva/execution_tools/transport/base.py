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
Defines the core transport abstraction for Semantiva's distributed execution runtime.
The transport layer moves `(data, context)` payloads between orchestrators and workers,
enabling pluggable, high-performance messaging (in-memory, NATS, Kafka, etc.).

Key concepts:
  - Message: encapsulates payload, context metadata, and an optional ack callback.
  - Subscription: sync/async iterable over incoming messages with lifecycle control.
  - SemantivaTransport: abstract interface for connecting, publishing, and subscribing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Iterator, AsyncIterator, NamedTuple
from concurrent.futures import Future
from semantiva.context_processors import ContextType


class Message(NamedTuple):
    """
    A single transport message carrying data, context, and optional metadata.

    Attributes:
        data:     The main data object.
        context:  Structured context accompanying the data.
        metadata: Transport-specific metadata (headers, chunk info, etc.).
        ack:      A callable to acknowledge receipt (for durable transports).
    """

    data: Any
    context: ContextType
    metadata: Dict[str, Any]
    ack: Callable[[], None]  # call to acknowledge receipt


class Subscription(ABC):
    """
    Represents an open subscription to a channel or topic.

    Provides both synchronous and asynchronous iterators over incoming Messages,
    plus a `close()` method to cancel the subscription and release resources.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[Message]:
        """
        Blocking iterator of incoming messages.

        Yields:
            Message: next received message until subscription is closed.
        """
        ...

    @abstractmethod
    async def __aiter__(self) -> AsyncIterator[Message]:
        """
        Asynchronous iterator of incoming messages.

        Yields:
            Message: next received message until subscription is closed.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Unsubscribe / stop listening and clean up any background resources.
        """
        ...


class SemantivaTransport(ABC):
    """
    Abstract base for all Semantiva transport implementations.

    Transports handle connection lifecycle, message serialization,
    and low-level publish/subscribe semantics. Concrete subclasses
    might wrap in-memory queues, NATS, Kafka, Redis, or shared memory.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Open connections or initialize client resources.

        Called by orchestrators and workers before publishing/subscribing.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Tear down connections, stop background threads, and clean up.

        Ensures a graceful shutdown of the transport layer.
        """
        ...

    @abstractmethod
    def publish(
        self,
        channel: str,
        data: Any,
        context: ContextType,
        metadata: Optional[Dict[str, Any]] = None,
        require_ack: bool = False,
    ) -> Optional[Future]:
        """
        Publish a message to the specified channel.

        Args:
            channel:      Subject or topic name to publish to.
            data:         Payload to send (arbitrary Python object).
            context:      Context dictionary or object to accompany data.
            metadata:     Optional transport-specific metadata (defaults to {}).
            require_ack:  If True, return a Future that resolves when
                          the transport confirms durable receipt.

        Returns:
            Future if require_ack=True, otherwise None.
        """
        ...

    @abstractmethod
    def subscribe(
        self, channel: str, *, callback: Optional[Callable[[Message], None]] = None
    ) -> Subscription:
        """
        Subscribe to messages on the given channel.

        Args:
            channel:  Subject or topic name (supports wildcards, patterns).
            callback: Optional function to call for each incoming Message.
                      If provided, the Subscription’s iterator need not be used.

        Returns:
            Subscription: an iterable over incoming messages, or a
            subscription that pushes messages to the callback in the background.
        """
        ...
