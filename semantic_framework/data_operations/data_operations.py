from typing import Any
from abc import ABC, abstractmethod
from ..context_operations.context_operations import ContextObserver

class BaseDataOperation(ABC):

    @abstractmethod
    def input_data_type(self):
        ...

    @abstractmethod
    def _operation(self, data, *args, **kwargs):
        ...

    def process(self, data,  *args, **kwargs):
        return self._operation(data, *args, **kwargs)
    
    def __call__(self, data,  *args, **kwargs):
        return self.process(data, *args, **kwargs)
    

class DataAlgorithm(BaseDataOperation):
    context_observer: ContextObserver

    @abstractmethod
    def output_data_type(self):
        ...

    def _notify_context_update(self, key: str, value: Any):
        self.context_observer.context["key"] = value

    def __init__(self, context_observer: ContextObserver):
        self.context_observer = context_observer

class DataProbe(BaseDataOperation):
    ...
