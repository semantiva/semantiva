from typing import Any
from abc import ABC, abstractmethod

class BaseDataType(ABC):
    _data: Any


    def __init__(self, data: Any):
        self._data = data

class DataSequence(BaseDataType):
    @abstractmethod
    def sequence_base_type(self):
        