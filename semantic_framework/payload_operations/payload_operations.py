from ..payload_operations.payload_operations import ContextObserver
from ..data_operations.data_operations import BaseDataOperation, DataAlgorithm, DataProbe
from typing import List, Any


class PayloadOperation(ContextObserver):
    ...

class Node(PayloadOperation):
    data_operation: BaseDataOperation


class Pipeline(PayloadOperation):
    ...


class AlgorithmNode(Node):
    data_operation: DataAlgorithm



class ProbeNode(Node):
    data_operation: DataProbe


class ProbeContextInjectornode(Node):
    context_keyword: str

class ProbeResultColectorNode(Node):
    _probed_data: List[Any]