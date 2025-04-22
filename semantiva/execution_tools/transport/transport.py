from abc import ABC, abstractmethod
from collections import defaultdict, deque
from typing import Iterator, Tuple
from semantiva.data_types import BaseDataType
from semantiva.context_processors.context_types import ContextType


class SemantivaTransport(ABC):
    """
    Abstracts how (data, context) tuples move between nodes.
    Responsibilities:
      - publish(subject, data, context)
      - subscribe(subject) -> stream of (data, context)
    """

    @abstractmethod
    def publish(
        self, subject: str, data: BaseDataType, context: ContextType
    ) -> None: ...

    @abstractmethod
    def subscribe(self, subject: str) -> Iterator[Tuple[BaseDataType, ContextType]]: ...


class InMemorySemantivaTransport(SemantivaTransport):
    """
    In-process transport for development and backward compatibility.
    Queues messages in memory by subject.
    """

    _deques: dict[str, deque]

    def __init__(self) -> None:
        self._queues: dict[str, deque[Tuple[BaseDataType, ContextType]]] = defaultdict(
            deque
        )

    def publish(self, subject: str, data: BaseDataType, context: ContextType) -> None:
        self._queues[subject].append((data, context))

    def subscribe(self, subject: str) -> Iterator[Tuple[BaseDataType, ContextType]]:
        queue = self._queues[subject]
        while queue:
            yield queue.popleft()
