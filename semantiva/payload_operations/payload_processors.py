from abc import ABC, abstractmethod
from typing import Any, Optional
from ..context_processors.context_types import ContextType
from ..context_processors.context_observer import ContextObserver
from ..data_types.data_types import BaseDataType, NoDataType
from ..logger import Logger


class PayloadProcessor(ContextObserver, ABC):
    """
    Base class for operations involving payloads in the semantic framework.

    This class extends ContextObserver to incorporate context management capabilities
    into payload-related operations.

    Attributes:
        context (dict): Inherited from ContextObserver, stores context key-value pairs.
        data (BaseDataType): An instance of a class derived from BaseDataType.
    """

    logger: Logger

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__()
        if logger:
            # If a logger instance is provided, use it
            self.logger = logger
        else:
            # If no logger is provided, create a new Logger instance
            self.logger = Logger()

    @abstractmethod
    def _process(self, data: BaseDataType, context: ContextType): ...

    def process(
        self,
        data: BaseDataType | None = None,
        context: ContextType | dict[Any, Any] | None = None,
    ) -> tuple[BaseDataType, ContextType]:
        """
        Public method to execute the payload processing logic.

        This method serves as an entry point to invoke the concrete implementation
        of the `_process` method, which must be defined in subclasses.

        Args:
            *args: Variable-length positional arguments to be passed to the `_process` method.
            **kwargs: Variable-length keyword arguments to be passed to the `_process` method.

        Returns:
            Any: The result of the `_process` method, as determined by the subclass implementation.

        Raises:
            NotImplementedError: If the `_process` method is not implemented in a subclass.
        """
        context = context or {}
        data = data or NoDataType()
        context_ = ContextType(context) if isinstance(context, dict) else context
        assert isinstance(
            context_, ContextType
        ), f"Context must be a dictionary of an instance of `ContextType`. Got {type(context)}"
        return self._process(data, context_)
