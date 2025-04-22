from abc import ABC, abstractmethod
from typing import List, Tuple
from semantiva.data_types import BaseDataType
from semantiva.context_processors.context_types import ContextType
from semantiva.execution_tools.executor.executor import SemantivaExecutor
from semantiva.execution_tools.executor.executor import SequentialSemantivaExecutor
from semantiva.execution_tools.transport import SemantivaTransport
from semantiva.payload_operations.nodes.nodes import PipelineNode
from semantiva.logger import Logger


class SemantivaOrchestrator(ABC):
    """
    Abstracts control-plane execution of a Pipeline.
    """

    @abstractmethod
    def execute(
        self,
        nodes: List[PipelineNode],
        data: BaseDataType,
        context: ContextType,
        transport: SemantivaTransport,
        logger: Logger,
    ) -> Tuple[BaseDataType, ContextType]: ...


class LocalSemantivaOrchestrator(SemantivaOrchestrator):
    def __init__(self, executor: SemantivaExecutor | None = None):
        self.executor = executor or SequentialSemantivaExecutor()

    def execute(
        self, nodes, data, context, transport, logger
    ) -> Tuple[BaseDataType, ContextType]:

        for index, node in enumerate(nodes, start=1):
            logger.debug(
                f"Orchestrator executing node {index}: {node.processor.__class__.__name__}"
            )
            data, context = node.process(data, context)

            # Publish to transport after node execution
            transport.publish(node.processor.semantic_id(), data, context)

        return data, context
